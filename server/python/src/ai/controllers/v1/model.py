"""模型列表控制器

提供模型列表查询接口。
"""

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.schemas.model import ModelListResponse, ProviderItem
from ai_plugin.sdk.entities.model import ModelType
from framework.common.ctx import get_tenant_id
from framework.database.dependencies import get_db_session

_logger = logger.bind(name=__name__)

router = APIRouter(prefix="/models", tags=["模型列表"])


@router.get("", response_model=ModelListResponse)
async def list_models(
    session: AsyncSession = Depends(get_db_session),
) -> ModelListResponse:
    """获取模型列表

    返回当前租户可用的所有提供商和模型。
    按提供商分组，每个提供商包含其可用模型列表。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return ModelListResponse(providers=[])

    try:
        factory = ModelProviderFactory(tenant_id)
        providers = await factory.get_providers()

        provider_items = []
        for provider in providers:
            if not provider.models:
                continue

            # 过滤 LLM 类型模型
            llm_models = [
                model for model in provider.models if model.model_type == ModelType.LLM
            ]

            if llm_models:
                # 提取图标 URL（优先使用 zh_Hans，fallback 到 en_US）
                icon_small = None
                icon_large = None
                if provider.icon_small:
                    icon_small = provider.icon_small.zh_Hans or provider.icon_small.en_US
                if provider.icon_large:
                    icon_large = provider.icon_large.zh_Hans or provider.icon_large.en_US

                provider_items.append(
                    ProviderItem.from_entity(
                        provider_id=provider.provider,
                        provider_label=provider.label,
                        models=llm_models,
                        icon_small=icon_small,
                        icon_large=icon_large,
                    )
                )

        return ModelListResponse(providers=provider_items)

    except Exception:
        _logger.exception("获取模型列表失败")
        return ModelListResponse(providers=[])
