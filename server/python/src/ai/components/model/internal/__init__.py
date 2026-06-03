"""
AI 模型组件内部实现

此包包含模型组件的内部实现细节，不应直接被外部模块导入。
"""

# 注意：由于存在循环导入问题，这里只导入实体类
# 其他模块需要在使用时单独导入
from ai.components.model.internal.entities.provider_entities import (
    CustomConfiguration,
    CustomModelConfiguration,
    CustomProviderConfiguration,
    ModelSettings,
)
from ai.components.model.internal.model_instance_factory import (
    ModelInstance,
    ModelInstanceFactory,
)

__all__ = [
    # Entities
    "CustomConfiguration",
    "CustomModelConfiguration",
    "CustomProviderConfiguration",
    "ModelSettings",
    # Factory
    "ModelInstance",
    "ModelInstanceFactory",
]
