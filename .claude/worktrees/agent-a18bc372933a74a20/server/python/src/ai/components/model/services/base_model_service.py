"""
大语言模型服务基类

迁移自 Alon: src/alon/components/model/services/base_model_service.py

提供所有模型服务的公共基础功能
"""

from ai.components.model.internal.model_instance_factory import ModelInstanceFactory
from ai_plugin.sdk.entities.model import ModelType


class BaseModelService:
    """
    模型服务基类

    提供所有模型服务的公共基础功能
    """

    def __init__(self, tenant_id: str):
        """
        初始化模型服务

        :param tenant_id: 租户 ID
        """
        self._factory = ModelInstanceFactory()
        self._tenant_id = tenant_id

    async def _resolve_default_model(self, model_type: ModelType) -> tuple[str, str]:
        """
        解析默认供应商和模型

        :param model_type: 模型类型
        :return: (供应商名称, 模型名称) 元组
        """
        # 首先尝试获取指定模型的默认供应商
        (
            default_provider,
            default_model,
        ) = await self._factory.get_default_provider_model_name(
            tenant_id=self._tenant_id,
            model_type=model_type,
        )

        if default_provider and default_model:
            # 如果有默认模型，但用户指定了不同的模型名称，仍使用默认供应商
            return default_provider, default_model

        # 如果没有默认模型，抛出异常
        raise ValueError(
            f"没有为 {model_type.value} 类型配置默认供应商，请明确指定供应商名称"
        )
