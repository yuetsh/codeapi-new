import subprocess

import sqlparse

TIMEOUT_SECONDS = 5

CLANG_FORMAT_STYLE = "{BasedOnStyle: LLVM, IndentWidth: 4, BreakBeforeBraces: Attach}"


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


def _format_with_sql(code: str) -> str:
    # sqlparse 对语法错误宽容，不会抛异常，语法问题留给判题阶段反馈
    # strip_whitespace 会把多条语句压成一行，先按分号拆分再逐条格式化
    statements = sqlparse.split(code)
    return "\n\n".join(
        sqlparse.format(s, strip_whitespace=True, keyword_case="upper")
        for s in statements
    )


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

    if language == "sql":
        return _format_with_sql(code)

    raise FormatError(f"不支持的语言: {language}")
