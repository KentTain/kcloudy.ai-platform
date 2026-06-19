from datetime import datetime

from pydantic import BaseModel


class BasePluginEntity(BaseModel):
    """
    插件实体基类

    所有插件相关实体的基础类，提供公共的ID和时间戳字段
    """

    id: str  # 插件实体的唯一标识符
    created_at: datetime  # 创建时间
    updated_at: datetime  # 最后更新时间
