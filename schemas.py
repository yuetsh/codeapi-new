from pydantic import BaseModel
from typing import List, Dict, Any


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
