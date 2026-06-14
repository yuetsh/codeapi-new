# 代码格式化（整理代码）功能设计

## 背景

`codenext` 编辑器支持 Python（含海龟绘图）、C、C++ 四种语言，目前没有一键格式化代码的功能。需要类似 Prettier 的"整理代码"按钮。

## 方案

后端 `codeapinew` 新增 `POST /format` 接口，按语言调用对应的格式化工具；前端在编辑器工具栏新增"整理代码"按钮调用该接口并替换编辑器内容。

### 后端

**Schema**（`schemas.py`）：

```python
class FormatRequest(BaseModel):
    code: str
    language: str  # python | turtle | c | cpp

class FormatResponse(BaseModel):
    code: str
```

**接口**（`main.py`）：

- `POST /format`
- `language` 为 `python` 或 `turtle` → 调用 `ruff format -`（通过 stdin/stdout 管道）
- `language` 为 `c` 或 `cpp` → 调用 `clang-format`，使用自定义 style：
  `-style="{BasedOnStyle: LLVM, IndentWidth: 4, BreakBeforeBraces: Allman}"`
  （贴近现有模板的 4 空格缩进 + Allman 大括号风格）
- 用 `subprocess.run`，设置超时（5 秒）
- 工具返回非零退出码（语法错误等）时，返回 HTTP 400，附带 stderr 作为错误信息；原代码不受影响

### 依赖

- `pyproject.toml` 增加 `ruff` 依赖（同步更新 `requirements.txt`）
- `Dockerfile` 的 `apt-get install` 增加 `clang-format`

### 前端（`codenext`）

- `src/api.ts` 新增 `formatCode(code: string, language: LANGUAGE)`，调用 `POST /format`
- `src/composables/code.ts` 新增 `format()`：调用接口成功后替换 `code.value`（自动触发已有的 localStorage 缓存逻辑）；失败时抛出错误供调用方提示
- `src/desktop/CodeSection.vue` 的 `#actions` 插槽中增加"整理代码"按钮（位于"复制"和"清空"之间），点击调用 `format()`，失败时通过 `useMessage().error(...)` 提示错误信息

## 错误处理

- 网络/接口错误或格式化失败：弹出错误提示，编辑器内容不变
- 超时：视为格式化失败，同样提示并保持原内容

## 范围

仅涉及 `codeapinew`（新增 `/format` 接口及依赖）和 `codenext`（新增按钮与调用逻辑）。移动端 `CodeEditor` 未使用 `label`，不渲染 `#actions` 插槽，与现有"调试"按钮一致，移动端不加入该功能。
