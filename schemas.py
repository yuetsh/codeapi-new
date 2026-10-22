from pydantic import BaseModel
from typing import List, Dict, Any, Literal


class PresetCodeCreate(BaseModel):
    """创建预设代码的请求模式"""

    code: str
    query: str


class PresetCodeResponse(BaseModel):
    """预设代码的响应模式"""

    id: int
    query: str
    code: str

    class Config:
        from_attributes = True


class AIAnalysisRequest(BaseModel):
    """AI 分析请求模式"""

    code: str
    language: str
    error_info: str


class DebugRequest(BaseModel):
    """调试请求模式，用于调试 Python 代码"""

    code: str
    inputs: List[str]


class FormatRequest(BaseModel):
    """格式化代码的请求模式"""

    code: str
    language: str


class FormatResponse(BaseModel):
    """格式化代码的响应模式"""

    code: str


class RunRequest(BaseModel):
    """运行 C/C++ 代码的请求模式"""

    code: str
    language: Literal["c", "cpp"]
    stdin: str = ""


class RunResponse(BaseModel):
    """运行结果，status 沿用 Judge0 的状态码：3 成功、6 编译错误、11 运行错误"""

    status: int
    output: str
