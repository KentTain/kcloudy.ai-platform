"""
模型管理服务

迁移自 Alon: src/alon/components/model/services/management_service.py

提供所有模型和供应商管理相关功能的统一接口
"""

from __future__ import annotations

from loguru import logger

from ai.components.model.internal.provider_manager import ProviderManager
from ai_plugin.sdk.entities.model import ModelType

_logger = logger.bind(name=__name__)


class ManagementService:
    """
    模型管理服务类

    封装所有模型和供应商管理相关的操作，提供简洁易用的接口
    """

    def __init__(self, tenant_id: str):
        """
        初始化模型管理服务

        :param tenant_id: 租户 ID
        """
        self._provider_manager = ProviderManager()
        self._tenant_id = tenant_id

    # ===== 模型相关管理 =====

    def models(
        self, model_type: ModelType | None = None, provider: str | None = None
    ) -> ModelService:
        """
        获取模型管理器

        :param model_type: 模型类型（可选）
        :param provider: 供应商名称（可选）
        :return: 模型管理器
        """
        return ModelService(
            self._provider_manager, self._tenant_id, model_type, provider
        )

    def providers(self) -> ProviderService:
        """
        获取供应商管理器

        :return: 供应商管理器
        """
        return ProviderService(self._provider_manager, self._tenant_id)


class ModelService:
    """模型管理器"""

    def __init__(
        self,
        provider_manager: ProviderManager,
        tenant_id: str,
        model_type: ModelType | None = None,
        provider: str | None = None,
    ):
        self._provider_manager = provider_manager
        self._tenant_id = tenant_id
        self._model_type = model_type
        self._provider = provider

    async def enable_model(
        self, provider: str, model: str, model_type: ModelType
    ) -> None:
        """
        启用模型

        :param provider: 供应商名称
        :param model: 模型名称
        :param model_type: 模型类型
        """
        provider_configurations = await self._provider_manager.get_configurations(
            self._tenant_id
        )
        provider_configuration = provider_configurations.get(provider)
        if not provider_configuration:
            raise ValueError(f"供应商 {provider} 不存在")

        await provider_configuration.enable_model(model=model, model_type=model_type)

    async def disable_model(
        self, provider: str, model: str, model_type: ModelType
    ) -> None:
        """
        禁用模型

        :param provider: 供应商名称
        :param model: 模型名称
        :param model_type: 模型类型
        """
        provider_configurations = await self._provider_manager.get_configurations(
            self._tenant_id
        )
        provider_configuration = provider_configurations.get(provider)
        if not provider_configuration:
            raise ValueError(f"供应商 {provider} 不存在")

        await provider_configuration.disable_model(model=model, model_type=model_type)

    async def custom_model_credentials_validate(
        self,
        tenant_id: str,
        provider: str,
        model_type: ModelType,
        model: str,
        credentials: dict,
    ) -> dict | None:
        """
        验证供应商凭证

        :param tenant_id: 租户 ID
        :param provider: 供应商名称
        :param model_type: 模型类型
        :param model: 模型名称
        :param credentials: 凭证信息
        :return: 验证结果
        """
        try:
            configurations = await self._provider_manager.get_configurations(tenant_id)
            provider_config = configurations.get(provider)
            if provider_config:
                credentials = await provider_config.custom_model_credentials_validate(
                    model_type, model, credentials
                )
                return credentials

            _logger.error(f"供应商 {provider} 不存在")
        except Exception as e:
            _logger.error(f"模型 {model} 凭证验证失败: {e}")
            return None

        return None


class ProviderService:
    """供应商管理器"""

    def __init__(self, provider_manager: ProviderManager, tenant_id: str):
        self._provider_manager = provider_manager
        self._tenant_id = tenant_id

    async def get_configurations(self):
        """
        获取供应商配置

        :return: 供应商配置对象
        """
        return await self._provider_manager.get_configurations(self._tenant_id)
