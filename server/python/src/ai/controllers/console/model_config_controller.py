"""
AI 模块控制台模型配置控制器

提供模型配置页面的数据聚合、模型启用/禁用、默认模型管理等功能。
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.model_config import (
    BatchSetDefaultModelRequest,
    EnabledModelsRequest,
)
from ai.services.model_config_service import model_config_service
from framework.common.exceptions import BadRequestError
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.dependencies import require_permission

_logger = logger.bind(name=__name__)

router = APIRouter(tags=["控制台-模型配置"])


@router.get(
    "/overview",
    summary="获取模型配置页面聚合数据",
    response_class=ORJSONResponse,
)
async def get_model_config_overview(
    session: AsyncSession = Depends(get_db_session),
    _=Depends(require_permission("ai:plugin:read")),
) -> ORJSONResponse:
    """
    获取模型配置页面的聚合数据，包括统计卡片、默认模型、插件模型列表。
    """
    from framework.common.ctx import get_tenant_id

    try:
        tenant_id = get_tenant_id()
        overview = await model_config_service.get_overview(session, tenant_id)
        return ApiResponse.success(data=overview.model_dump())
    except Exception as e:
        _logger.exception("获取模型配置概览失败")
        raise BadRequestError(f"获取模型配置概览失败: {str(e)}")


@router.get(
    "/plugins/{plugin_id}/available-models",
    summary="获取插件可用模型列表",
    response_class=ORJSONResponse,
)
async def get_available_models(
    plugin_id: str = Path(..., description="插件 ID"),
    session: AsyncSession = Depends(get_db_session),
    _=Depends(require_permission("ai:plugin:read")),
) -> ORJSONResponse:
    """
    获取指定插件声明的所有模型，含启用状态。
    """
    from framework.common.ctx import get_tenant_id

    try:
        tenant_id = get_tenant_id()
        result = await model_config_service.get_available_models(
            session, tenant_id, plugin_id
        )
        return ApiResponse.success(data=result.model_dump())
    except Exception as e:
        _logger.exception("获取插件可用模型失败")
        raise BadRequestError(f"获取插件可用模型失败: {str(e)}")


@router.post(
    "/plugins/{plugin_id}/enabled-models",
    summary="配置插件启用的模型",
    response_class=ORJSONResponse,
)
async def set_enabled_models(
    plugin_id: str = Path(..., description="插件 ID"),
    data: EnabledModelsRequest = Body(..., description="启用的模型列表"),
    session: AsyncSession = Depends(get_db_session),
    _=Depends(require_permission("ai:plugin:write")),
) -> ORJSONResponse:
    """
    配置指定插件下要启用哪些模型。
    """
    from framework.common.ctx import get_tenant_id

    try:
        tenant_id = get_tenant_id()
        await model_config_service.set_enabled_models(
            session, tenant_id, plugin_id, data.model_names
        )
        return ApiResponse.success()
    except Exception as e:
        _logger.exception("配置插件启用模型失败")
        raise BadRequestError(f"配置插件启用模型失败: {str(e)}")


@router.get(
    "/models",
    summary="按类型获取可选模型",
    response_class=ORJSONResponse,
)
async def get_models_by_type(
    model_type: str = Query(..., description="模型类型"),
    session: AsyncSession = Depends(get_db_session),
    _=Depends(require_permission("ai:plugin:read")),
) -> ORJSONResponse:
    """
    按模型类型获取所有可选模型列表，含插件 ID 和供应商信息。
    用于设置默认模型弹窗。
    """
    from framework.common.ctx import get_tenant_id

    try:
        tenant_id = get_tenant_id()
        models = await model_config_service.get_models_by_type(
            session, tenant_id, model_type
        )
        return ApiResponse.success(data=[m.model_dump() for m in models])
    except Exception as e:
        _logger.exception("获取可选模型列表失败")
        raise BadRequestError(f"获取可选模型列表失败: {str(e)}")


@router.post(
    "/default-models/batch",
    summary="批量设置默认模型",
    response_class=ORJSONResponse,
)
async def batch_set_default_models(
    data: BatchSetDefaultModelRequest = Body(..., description="批量设置默认模型请求"),
    session: AsyncSession = Depends(get_db_session),
    _=Depends(require_permission("ai:plugin:write")),
) -> ORJSONResponse:
    """
    批量设置默认模型。embedding 和 rerank 必须来自同一插件。
    如果该类型已有默认模型，会返回错误，默认模型设置后不可更改。
    """
    from framework.common.ctx import get_tenant_id

    try:
        tenant_id = get_tenant_id()
        items = [item.model_dump() for item in data.items]
        await model_config_service.batch_set_default_models(session, tenant_id, items)
        return ApiResponse.success()
    except ValueError as e:
        raise BadRequestError(str(e))
    except Exception as e:
        _logger.exception("批量设置默认模型失败")
        raise BadRequestError(f"批量设置默认模型失败: {str(e)}")


