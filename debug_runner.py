"""在独立子进程中执行 Python Tutor 跟踪。

pg_logger 是在 API 进程内直接跑用户代码的：它会替换全局 sys.stdout、
用模块级全局变量 input_string_queue 传输入，并且 MAX_EXECUTED_LINES 只能
限制"行事件"数量，挡不住 sum(range(10**9)) 这种单行重计算。因此这里把
执行整体挪进子进程：

- 子进程内 setrlimit 限制 CPU 和内存（SIGXCPU 只会杀子进程）；
- 父进程再加一层墙钟超时，兜住 time.sleep 这类不耗 CPU 的挂起；
- 全局 stdout / input_string_queue 天然按请求隔离，可以安全并发。

本文件同时是父进程的调用入口和子进程的脚本入口：
    python debug_runner.py <请求 json> <结果 json>
"""

import json
import os
import subprocess
import sys
import tempfile

# 子进程资源上限
CPU_LIMIT_SECONDS = 5
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
# 父进程墙钟上限，要比 CPU 上限宽，留出解释器启动和跟踪开销
WALL_TIMEOUT_SECONDS = 15

# SIGXCPU / SIGKILL 对应的返回码（subprocess 用负数表示被信号终止）
_SIGXCPU_RETURNCODE = -24
_SIGKILL_RETURNCODE = -9


class DebugError(Exception):
    """调试执行失败，消息可直接展示给用户"""


# ==================== 父进程 ====================
def run_debug(code: str, inputs: list[str]) -> dict:
    """在子进程里跟踪执行 code，返回 {"code": ..., "trace": [...]}"""
    with tempfile.TemporaryDirectory(prefix="debug-") as workdir:
        request_path = os.path.join(workdir, "request.json")
        result_path = os.path.join(workdir, "result.json")

        with open(request_path, "w", encoding="utf-8") as f:
            json.dump({"code": code, "inputs": inputs}, f)

        try:
            proc = subprocess.run(
                [sys.executable, __file__, request_path, result_path],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                timeout=WALL_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise DebugError(
                f"代码运行超过 {WALL_TIMEOUT_SECONDS} 秒，请检查是否有死循环或长时间等待"
            )

        if proc.returncode == _SIGXCPU_RETURNCODE:
            raise DebugError(
                f"代码占用 CPU 超过 {CPU_LIMIT_SECONDS} 秒，请减少计算量或循环次数"
            )
        if proc.returncode == _SIGKILL_RETURNCODE:
            raise DebugError("代码占用资源过多，已被终止")

        if not os.path.exists(result_path):
            stderr = proc.stderr.decode("utf-8", "replace").strip()
            raise DebugError(f"调试进程异常退出：{stderr[-500:] or '无输出'}")

        with open(result_path, encoding="utf-8") as f:
            result = json.load(f)

    if "error" in result:
        raise DebugError(result["error"])
    return result


# ==================== 子进程 ====================
def _apply_limits() -> None:
    try:
        import resource
    except ImportError:  # 非 POSIX 平台，跳过
        return

    # 软硬限之间留出差值：软限先发 SIGXCPU（可识别成"CPU 超时"），
    # 若同时设成一样的值，内核会直接发 SIGKILL，就分辨不出原因了
    resource.setrlimit(
        resource.RLIMIT_CPU, (CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS + 2)
    )
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))


def _main() -> None:
    request_path, result_path = sys.argv[1], sys.argv[2]

    with open(request_path, encoding="utf-8") as f:
        request = json.load(f)

    # 先把结果文件打开，避免用户代码耗尽资源后写不出结果
    result_file = open(result_path, "w", encoding="utf-8")

    # 在设限之前完成导入，用户代码执行期间不再需要读文件系统
    from pg_logger import exec_script_str_local

    data: dict = {}

    def dump(input_code, output_trace):
        data.update(code=input_code, trace=output_trace)

    _apply_limits()

    try:
        exec_script_str_local(request["code"], request["inputs"], False, False, dump)
    except MemoryError:
        data = {"error": "代码占用内存过多，请减少数据规模"}
    except RecursionError:
        data = {"error": "递归层数过深，请检查递归的终止条件"}
    except BaseException as e:  # 跟踪器自身出错，不能让它变成 500
        data = {"error": f"调试执行失败：{type(e).__name__}: {e}"}

    if not data:
        data = {"error": "调试执行失败：未生成跟踪数据"}

    json.dump(data, result_file)
    result_file.close()


if __name__ == "__main__":
    _main()
