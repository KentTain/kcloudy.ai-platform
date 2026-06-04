"""模型列表控制器

提供模型列表查询接口。
"""

from fastapi import APIRouter
from loguru import logger

from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.schemas.model import ModelListResponse
from framework.common.ctx import get_tenant_id

_logger = logger.bind(name=__name__)

router = APIRouter(prefix="/models", tags=["模型列表"])


@router.get("", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """获取模型列表

    返回当前租户可用的所有提供商和模型。
    按提供商分组，每个提供商包含其可用模型列表。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        # 未登录时返回空列表
        return ModelListResponse(providers=[])

    try:
        factory = ModelProviderFactory(tenant_id)
        providers = await factory.get_providers()

        provider_items = []
        for provider in providers:
            # 只处理有模型的提供商
            if not provider.models:
                continue

            model_items = []
            for model in provider.models:
                # 只处理 LLM 类型模型
                from ai_plugin.sdk.entities.model import ModelType

                if model.model_type != ModelType.LLM:
                    continue

                # 获取模型描述（优先使用中文标签）
                description = model.label.zh_Hans or model.label.en_US

                model_items.append(
                    {
                        "id": f"{provider.provider}/{model.model}",
                        "name": model.model,
                        "description": description,
                    }
                )

            if model_items:
                # 获取提供商显示名称（优先使用中文标签）
                provider_name = provider.label.zh_Hans or provider.label.en_US

                provider_items.append(
                    {
                        "id": provider.provider,
                        "name": provider_name,
                        "models": model_items,
                    }
                )

        return ModelListResponse(providers=provider_items)

    except Exception as e:
        _logger.exception("获取模型列表失败")
        return ModelListResponse(providers=[])
