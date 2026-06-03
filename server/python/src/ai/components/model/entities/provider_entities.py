from pydantic import BaseModel


class SimpleProviderConfig(BaseModel):
    """
    供应商配置实体类
    """

    provider: str
    credentials: dict
