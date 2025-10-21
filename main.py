from io import StringIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import json
from openai import OpenAI
from schemas import PresetCodeCreate, AIAnalysisRequest, DebugRequest
from database import DatabaseService
from pg_logger import exec_script_str_local
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

app = FastAPI(title="Code API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://code.xuyue.cc",
        "http://10.13.114.114",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
DATABASE_URL = "sqlite://database.db"

# 初始化数据库
DatabaseService.init_database(app, DATABASE_URL)


@app.get("/")
async def get_all_codes() -> dict:
    """获取所有预设代码"""
    codes = await DatabaseService.get_all_codes()
    return {"data": codes}


@app.get("/query/{query}")
async def get_code_by_query(query: str) -> dict:
    """根据查询字符串获取特定代码"""
    code = await DatabaseService.get_code_by_query(query)
    if not code:
        raise HTTPException(status_code=404, detail="Record not found!")
    return {"data": code}


@app.post("/")
async def create_code(code_data: PresetCodeCreate) -> dict:
    """创建新的预设代码"""
    try:
        code = await DatabaseService.create_code(code_data)
        return {"data": code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/{code_id}")
async def delete_code(code_id: int) -> dict:
    """删除指定 ID 的代码"""
    success = await DatabaseService.delete_code(code_id)
    if not success:
        raise HTTPException(status_code=400, detail="Record not found!")

    return {"data": True}


@app.post("/ai")
async def ai_analysis(request: AIAnalysisRequest):
    """AI 代码分析端点"""
    code = request.code
    error_info = request.error_info
    language = request.language

    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="API_KEY is not set")

    system_prompt = "你是编程老师，擅长分析代码和错误信息，一般出错在语法和格式，请指出错误在第几行，并给出中文的、简要的解决方法。用 markdown 格式返回。"
    user_prompt = f"编程语言：{language}\n代码：\n```{language}\n{code}\n```\n错误信息：\n```\n{error_info}\n```"

    def generate_response():
        try:
            # 初始化 OpenAI 客户端
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

            # 创建流式响应
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                seed=0,
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield f"data: {json.dumps({'event': 'chunk', 'data': delta.content})}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'event': 'done', 'data': ''})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/debug")
async def debug(request: DebugRequest):
    """调试端点"""
    code = request.code
    inputs = request.inputs

    data = {}

    def dump(input_code, output_trace):
        data.update(dict(code=input_code, trace=output_trace))

    exec_script_str_local(code, inputs, False, False, dump)
    return {"data": data}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8080)
