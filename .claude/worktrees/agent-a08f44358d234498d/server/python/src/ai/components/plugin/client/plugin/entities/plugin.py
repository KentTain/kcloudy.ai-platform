"""
插件实体类

注意：Provider ID 相关类（GenericProviderID、ModelProviderID、ToolProviderID）
已移动到 ai.components.model.schema.provider_id 模块，此处仅为向后兼容重新导出。
"""

# 从新位置导入 Provider ID 类
from ai.components.model.schema.provider_id import (
    GenericProviderID,
    ModelProviderID,
    ProviderIDFormatError,
    ToolProviderID,
)

# 重新导出以保持向后兼容
__all__ = [
    "GenericProviderID",
    "ModelProviderID",
    "ProviderIDFormatError",
    "ToolProviderID",
]
