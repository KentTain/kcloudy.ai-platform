"""
Pydantic 校验模型
"""

from framework.schemas import BaseModel


class SuccessRespModel(BaseModel):
    """成功响应模型"""

    code: int = 200
    msg: str = "success"
