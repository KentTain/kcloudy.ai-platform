"""
Pydantic 校验模型
"""

from pydantic import BaseModel


class SuccessRespModel(BaseModel):
    """成功响应模型"""

    code: int = 200
    msg: str = "success"
