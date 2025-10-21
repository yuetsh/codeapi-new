from tortoise.models import Model
from tortoise import fields

class PresetCode(Model):
    """预设代码数据库模型"""
    id = fields.IntField(pk=True)
    query = fields.CharField(max_length=255, unique=True)
    code = fields.TextField()
    
    class Meta:
        table = "preset_codes"
