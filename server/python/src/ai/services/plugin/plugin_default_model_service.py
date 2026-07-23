"""插件默认模型服务"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginDefaultModel

_logger = logger.bind(name=__name__)


class PluginDefaultModelService:
    """插件默认模型服务"""

    async def get_default_model(
        self,
        session: AsyncSession,
        tenant_id: str,
        model_type: str,
    ) -> PluginDefaultModel | None:
        """获取默认模型"""
        return await PluginDefaultModel.one_by_conditions(
            session,
            conditions=[
                PluginDefaultModel.tenant_id == tenant_id,
                PluginDefaultModel.model_type == model_type,
                PluginDefaultModel.is_valid == True,
            ],
        )

    async def set_default_model(
        self,
        session: AsyncSession,
        tenant_id: str,
        model_type: str,
        plugin_id: str,
        model_name: str | None = None,
        credential_id: str | None = None,
        custom_base_url: str | None = None,
        custom_model_name: str | None = None,
    ) -> PluginDefaultModel:
        """设置默认模型（upsert）"""
        existing = await self.get_default_model(session, tenant_id, model_type)

        if existing:
            existing.plugin_id = plugin_id
            existing.model_name = model_name
            existing.credential_id = credential_id
            existing.custom_base_url = custom_base_url
            existing.custom_model_name = custom_model_name
            existing.is_valid = True
            return existing
        else:
            return await PluginDefaultModel.create(
                session,
                tenant_id=tenant_id,
                model_type=model_type,
                plugin_id=plugin_id,
                model_name=model_name,
                credential_id=credential_id,
                custom_base_url=custom_base_url,
                custom_model_name=custom_model_name,
                is_valid=True,
            )

    async def clear_default_model(
        self,
        session: AsyncSession,
        tenant_id: str,
        model_type: str,
    ) -> None:
        """清除默认模型（软删除）"""
        existing = await self.get_default_model(session, tenant_id, model_type)
        if existing:
            existing.is_valid = False


plugin_default_model_service = PluginDefaultModelService()
