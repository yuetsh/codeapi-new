import os

import httpx

# go-judge 沙箱地址，docker-compose 里是 code-judge 容器
GOJUDGE_URL = os.getenv("GOJUDGE_URL", "http://code-judge:5050")

# 状态码沿用前端（原 Judge0）的约定
STATUS_ACCEPTED = 3
STATUS_COMPILE_ERROR = 6
STATUS_RUNTIME_ERROR = 11

SECOND = 1_000_000_000  # go-judge 的时间单位是纳秒
MB = 1024 * 1024
OUTPUT_MAX = 64 * 1024

LANGUAGES = {
    "c": {
        "source": "main.c",
        "compile": ["/usr/bin/gcc", "main.c", "-o", "main", "-lm"],
    },
    "cpp": {
        "source": "main.cpp",
        "compile": ["/usr/bin/g++", "main.cpp", "-o", "main"],
    },
}

STATUS_MESSAGES = {
    "Time Limit Exceeded": "运行超时",
    "Memory Limit Exceeded": "内存超出限制",
    "Output Limit Exceeded": "输出超出限制",
    "Signalled": "程序异常终止",
}


class RunError(Exception):
    """沙箱不可用等非用户代码导致的错误"""


def _cmd(args: list[str], stdin: str, cpu: int, memory: int, **extra) -> dict:
    return {
        "args": args,
        "env": ["PATH=/usr/bin:/bin"],
        "files": [
            {"content": stdin},
            {"name": "stdout", "max": OUTPUT_MAX},
            {"name": "stderr", "max": OUTPUT_MAX},
        ],
        "cpuLimit": cpu * SECOND,
        "clockLimit": cpu * 2 * SECOND,
        "memoryLimit": memory * MB,
        "procLimit": 50,
        "copyOut": ["stdout", "stderr"],
        **extra,
    }


async def _run(client: httpx.AsyncClient, cmd: dict) -> dict:
    try:
        response = await client.post("/run", json={"cmd": [cmd]})
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise RunError(f"判题沙箱不可用：{e}")
    result = response.json()[0]
    if result["status"] == "Internal Error":
        raise RunError(result.get("error") or "判题沙箱内部错误")
    return result


def _output(result: dict) -> str:
    # 与原来 Judge0 的 redirect_stderr_to_stdout 效果接近：stdout 在前，stderr 在后
    files = result.get("files", {})
    return (files.get("stdout", "") + files.get("stderr", "")).strip()


async def run_code(language: str, code: str, stdin: str) -> dict:
    config = LANGUAGES[language]
    async with httpx.AsyncClient(base_url=GOJUDGE_URL, timeout=30) as client:
        compiled = await _run(
            client,
            _cmd(
                config["compile"],
                "",
                cpu=10,
                memory=512,
                copyIn={config["source"]: {"content": code}},
                copyOutCached=["main"],
            ),
        )
        if compiled["status"] != "Accepted":
            return {"status": STATUS_COMPILE_ERROR, "output": _output(compiled)}

        file_id = compiled["fileIds"]["main"]
        try:
            result = await _run(
                client,
                _cmd(
                    ["main"],
                    stdin,
                    cpu=5,
                    memory=256,
                    copyIn={"main": {"fileId": file_id}},
                ),
            )
        finally:
            try:
                await client.delete(f"/file/{file_id}")
            except httpx.HTTPError:
                pass

    output = _output(result)
    if result["status"] == "Accepted":
        return {"status": STATUS_ACCEPTED, "output": output}
    message = STATUS_MESSAGES.get(result["status"])
    if message:
        output = f"{output}\n{message}".strip()
    return {"status": STATUS_RUNTIME_ERROR, "output": output}
