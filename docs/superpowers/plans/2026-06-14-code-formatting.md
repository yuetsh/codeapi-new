# 代码格式化（整理代码）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 `codenext` 编辑器增加"整理代码"按钮，后端通过 `POST /format` 调用 ruff（Python/海龟绘图）和 clang-format（C/C++）格式化代码。

**Architecture:** `codeapinew` 新增 `formatter.py`（封装 subprocess 调用 ruff/clang-format），`main.py` 新增 `/format` 端点；`codenext` 新增 `api.ts` 的 `formatCode`、`composables/code.ts` 的 `format()`，并在 `CodeSection.vue` 加按钮。

**Tech Stack:** FastAPI, Pydantic, subprocess, ruff (CLI), clang-format (CLI), Vue 3, axios, naive-ui

---

## Task 1: 后端依赖（ruff、pytest、clang-format）

**Files:**
- Modify: `codeapinew/pyproject.toml`
- Modify: `codeapinew/requirements.txt`
- Modify: `codeapinew/Dockerfile`

- [ ] **Step 1: 添加 ruff 为运行依赖**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv add ruff
```

Expected: `pyproject.toml` 的 `dependencies` 列表新增 `"ruff>=..."`，`uv.lock` 更新。

- [ ] **Step 2: 添加 pytest 为开发依赖**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv add --dev pytest
```

Expected: `pyproject.toml` 新增 `[dependency-groups]` / `dev = ["pytest>=..."]`。

- [ ] **Step 3: 查询已安装的 ruff 版本，同步到 requirements.txt**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv run ruff --version
```

记录输出的版本号（如 `ruff 0.8.x`），然后在 `requirements.txt` 中按字母序插入一行（例如插在 `pyyaml` 和 `pytz` 之间，requirements.txt 当前是字母序排列）：

```
ruff==<上一步输出的版本号>
```

- [ ] **Step 4: Dockerfile 中加入 clang-format**

修改 `codeapinew/Dockerfile` 中的 apt 安装步骤：

```dockerfile
# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    clang-format \
    && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 5: Commit**

```bash
cd /home/xuyue/Projects/Code/codeapinew && git add pyproject.toml uv.lock requirements.txt Dockerfile && git commit -m "build: add ruff and pytest dependencies, install clang-format in image"
```

---

## Task 2: `formatter.py` — 格式化核心逻辑（TDD）

**Files:**
- Create: `codeapinew/formatter.py`
- Test: `codeapinew/test_formatter.py`

- [ ] **Step 1: 写失败的测试**

创建 `codeapinew/test_formatter.py`：

```python
import pytest

from formatter import FormatError, format_code


def test_format_python_normalizes_spacing():
    result = format_code("x=1\n", "python")
    assert result == "x = 1\n"


def test_format_turtle_uses_python_formatter():
    result = format_code("t=1\n", "turtle")
    assert result == "t = 1\n"


def test_format_python_syntax_error_raises():
    with pytest.raises(FormatError):
        format_code("def foo(:\n", "python")


def test_format_c_uses_allman_braces():
    result = format_code("int main(){int x=1;return x;}", "c")
    assert result.rstrip("\n") == "int main()\n{\n    int x = 1;\n    return x;\n}"


def test_format_cpp_uses_allman_braces():
    result = format_code("class Foo{};", "cpp")
    assert result.rstrip("\n") == "class Foo\n{\n};"


def test_format_unsupported_language_raises():
    with pytest.raises(FormatError):
        format_code("print(1)", "java")
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv run pytest test_formatter.py -v
```

Expected: FAIL，`ModuleNotFoundError: No module named 'formatter'`（或 collection error）。

- [ ] **Step 3: 实现 `formatter.py`**

创建 `codeapinew/formatter.py`：

```python
import subprocess

TIMEOUT_SECONDS = 5

CLANG_FORMAT_STYLE = "{BasedOnStyle: LLVM, IndentWidth: 4, BreakBeforeBraces: Allman}"


class FormatError(Exception):
    """代码格式化失败时抛出，message 为可展示给用户的错误信息"""


def _run(cmd: list[str], code: str) -> str:
    try:
        result = subprocess.run(
            cmd,
            input=code,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise FormatError("格式化超时")

    if result.returncode != 0:
        raise FormatError(result.stderr.strip() or "格式化失败")

    return result.stdout


def format_code(code: str, language: str) -> str:
    if language in ("python", "turtle"):
        return _run(["ruff", "format", "-", "--stdin-filename", "main.py"], code)

    if language in ("c", "cpp"):
        ext = "c" if language == "c" else "cpp"
        return _run(
            [
                "clang-format",
                f"-style={CLANG_FORMAT_STYLE}",
                f"-assume-filename=main.{ext}",
            ],
            code,
        )

    raise FormatError(f"不支持的语言: {language}")
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv run pytest test_formatter.py -v
```

Expected: 全部 6 个测试 PASS。

- [ ] **Step 5: Commit**

```bash
cd /home/xuyue/Projects/Code/codeapinew && git add formatter.py test_formatter.py && git commit -m "feat: add formatter module wrapping ruff and clang-format"
```

---

## Task 3: `POST /format` 端点（TDD）

**Files:**
- Modify: `codeapinew/schemas.py`
- Modify: `codeapinew/main.py`
- Test: `codeapinew/test_main.py`

- [ ] **Step 1: 写失败的测试**

创建 `codeapinew/test_main.py`：

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_format_endpoint_formats_python_code():
    response = client.post("/format", json={"code": "x=1\n", "language": "python"})
    assert response.status_code == 200
    assert response.json() == {"code": "x = 1\n"}


def test_format_endpoint_returns_400_on_syntax_error():
    response = client.post(
        "/format", json={"code": "def foo(:\n", "language": "python"}
    )
    assert response.status_code == 400
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv run pytest test_main.py -v
```

Expected: FAIL，两个测试均得到 404（路由不存在）。

- [ ] **Step 3: 在 `schemas.py` 新增请求/响应模型**

在 `codeapinew/schemas.py` 末尾追加：

```python


class FormatRequest(BaseModel):
    """格式化代码的请求模式"""

    code: str
    language: str


class FormatResponse(BaseModel):
    """格式化代码的响应模式"""

    code: str
```

- [ ] **Step 4: 在 `main.py` 新增 `/format` 端点**

修改 `codeapinew/main.py` 第 8 行的导入，加入新模型：

```python
from schemas import (
    PresetCodeCreate,
    AIAnalysisRequest,
    DebugRequest,
    FormatRequest,
    FormatResponse,
)
```

在文件顶部其他导入旁加入：

```python
from formatter import format_code, FormatError
```

在 `/debug` 端点（第 127-139 行）之后新增：

```python
@app.post("/format", response_model=FormatResponse)
async def format_code_endpoint(request: FormatRequest) -> FormatResponse:
    """格式化代码"""
    try:
        formatted = format_code(request.code, request.language)
    except FormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return FormatResponse(code=formatted)
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv run pytest -v
```

Expected: 全部测试（`test_formatter.py` + `test_main.py`）PASS。

- [ ] **Step 6: Commit**

```bash
cd /home/xuyue/Projects/Code/codeapinew && git add schemas.py main.py test_main.py && git commit -m "feat: add POST /format endpoint"
```

---

## Task 4: 前端 API 客户端 `formatCode`

**Files:**
- Modify: `codenext/src/api.ts`

- [ ] **Step 1: 修改导入并新增 `formatCode`**

将 `codenext/src/api.ts` 第 3 行：

```ts
import { Code, Submission } from "./types"
```

改为：

```ts
import { Code, LANGUAGE, Submission } from "./types"
```

在文件末尾（`debug` 函数之后）新增：

```ts
export async function formatCode(code: string, language: LANGUAGE) {
  const res = await api.post("/format", { code, language })
  return res.data.code as string
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/xuyue/Projects/Code/codenext && git add src/api.ts && git commit -m "feat: add formatCode API client"
```

---

## Task 5: 前端状态 action `format()`

**Files:**
- Modify: `codenext/src/composables/code.ts`

- [ ] **Step 1: 修改导入并新增 `format` action**

将 `codenext/src/composables/code.ts` 第 5 行：

```ts
import { getCodeByQuery, submit } from "../api"
```

改为：

```ts
import { formatCode, getCodeByQuery, submit } from "../api"
```

在文件末尾（`share` 函数之后）新增：

```ts
export async function format() {
  code.value = await formatCode(code.value, code.language)
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/xuyue/Projects/Code/codenext && git add src/composables/code.ts && git commit -m "feat: add format action to code composable"
```

---

## Task 6: "整理代码"按钮（`CodeSection.vue`）+ 手动验证

**Files:**
- Modify: `codenext/src/desktop/CodeSection.vue`

- [ ] **Step 1: 修改导入**

将 `codenext/src/desktop/CodeSection.vue` 第 7 行：

```ts
import { code, input, reset, size } from "../composables/code"
```

改为：

```ts
import { code, format, input, reset, size } from "../composables/code"
```

- [ ] **Step 2: 新增 `handleFormat` 函数**

在 `copy` 函数（第 20-23 行）之后新增：

```ts
async function handleFormat() {
  try {
    await format()
    message.success("代码已整理")
  } catch (err: any) {
    message.error(
      `整理失败: ${err?.response?.data?.detail ?? err?.message ?? "未知错误"}`,
    )
  }
}
```

- [ ] **Step 3: 在 actions 插槽中加入按钮**

将模板中第 68-80 行的 `#actions` 插槽：

```vue
    <template #actions>
      <n-button quaternary type="primary" @click="copy">复制</n-button>
      <n-button quaternary @click="reset">清空</n-button>
      <n-button
        v-if="code.language === 'python'"
        quaternary
        type="error"
        :disabled="!code.value"
        @click="handleDebug"
      >
        调试
      </n-button>
    </template>
```

改为：

```vue
    <template #actions>
      <n-button quaternary type="primary" @click="copy">复制</n-button>
      <n-button quaternary @click="handleFormat">整理代码</n-button>
      <n-button quaternary @click="reset">清空</n-button>
      <n-button
        v-if="code.language === 'python'"
        quaternary
        type="error"
        :disabled="!code.value"
        @click="handleDebug"
      >
        调试
      </n-button>
    </template>
```

- [ ] **Step 4: 启动前后端，手动验证**

```bash
cd /home/xuyue/Projects/Code/codeapinew && uv run python main.py
```

```bash
cd /home/xuyue/Projects/Code/codenext && npm run start
```

打开 `http://localhost:3000`，对每种语言验证：

- Python：输入 `x=1\ny  =2`，点击"整理代码"，确认变为 `x = 1\ny = 2`，并提示"代码已整理"
- C：选择 C 语言，输入 `int main(){int x=1;return x;}`，点击"整理代码"，确认大括号换行（Allman 风格）、缩进 4 空格
- C++：同上，验证 `class Foo{};` 格式化结果
- 海龟绘图：输入含 `t=1` 的代码，验证按 Python 格式化
- 错误场景：输入语法错误的 Python（如 `def foo(:`），点击"整理代码"，确认弹出错误提示且编辑器内容不变

- [ ] **Step 5: Commit**

```bash
cd /home/xuyue/Projects/Code/codenext && git add src/desktop/CodeSection.vue && git commit -m "feat: add format code button to editor toolbar"
```

---

## Self-Review Notes

- Spec coverage: `/format` 接口（Task 2-3）、依赖安装（Task 1）、前端按钮与调用链（Task 4-6）、错误处理（Task 3 的 400 响应 + Task 6 的 message.error）、海龟绘图复用 python 格式化（Task 2/3 测试覆盖）均已覆盖。移动端按设计明确排除，无需任务。
- 类型一致性：`formatCode(code, language)` 在 `api.ts`、`composables/code.ts`、`formatter.py` 的 `format_code(code, language)` 参数顺序与命名一致；`FormatRequest`/`FormatResponse` 字段名 `code`/`language` 与前端请求体一致。
