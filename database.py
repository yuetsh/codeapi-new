from tortoise.contrib.fastapi import register_tortoise
from models import PresetCode
from schemas import PresetCodeCreate, PresetCodeResponse
from typing import List, Optional

class DatabaseService:
    """数据库操作服务类"""
    
    @staticmethod
    def init_database(app, database_url: str):
        """初始化数据库连接"""
        register_tortoise(
            app,
            db_url=database_url,
            modules={"models": ["models"]},
            generate_schemas=True,
        )
    
    @staticmethod
    async def get_all_codes() -> List[PresetCodeResponse]:
        """获取所有预设代码"""
        codes = await PresetCode.all().order_by('-id')
        return [PresetCodeResponse.from_orm(code).dict() for code in codes]
    
    @staticmethod
    async def get_code_by_query(query: str) -> Optional[PresetCodeResponse]:
        """根据查询字符串获取特定代码"""
        code = await PresetCode.get_or_none(query=query)
        if not code:
            return None
        return PresetCodeResponse.from_orm(code).dict()
    
    @staticmethod
    async def create_code(code_data: PresetCodeCreate) -> PresetCodeResponse:
        """创建新的预设代码"""
        code = await PresetCode.create(**code_data.dict())
        return PresetCodeResponse.from_orm(code).dict()
    
    @staticmethod
    async def delete_code(code_id: int) -> bool:
        """删除指定 ID 的代码"""
        code = await PresetCode.get_or_none(id=code_id)
        if not code:
            return False
        
        await code.delete()
        return True
