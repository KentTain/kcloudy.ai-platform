"""插件配置控制器

提供插件配置、测试、启动、停止等 HTTP 接口。

路由前缀：/ai/console/v1/plugins/installations/{plugin_id}
"""

from fastapi import APIRouter, Depends, Path
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.plugin_config import (
    PluginConfigRequest,
    PluginConfigResponse,
    PluginStartResponse,
    PluginStopResponse,
    PluginTestResponse,
)
from ai.services.plugin import plugin_config_service
from framework.common.ctx import get_tenant_id
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.dependencies import require_permission

_logger = logger.bind(name=__name__)

router = APIRouter(tags=["控制台-插件配置管理"])


@router.post(
    "/{plugin_id}/config",
    summary="配置插件",
    response_class=ORJSONResponse,
)
async def config_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    request: PluginConfigRequest = None,
    _perm: None = Depends(require_permission("ai:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    配置插件

    场景：用户配置插件的能力配置和运行时配置
    WHEN 请求 POST /ai/console/v1/plugins/installations/{plugin_id}/config
    THEN 保存配置并返回配置状态

    Args:
        plugin_id: 插件 ID
        request: 配置请求，包含 plugin_config 和 runtime_config
        session: 数据库会话

    Returns:
        PluginConfigResponse
    """
    try:
        tenant_id = get_tenant_id()
        if not tenant_id:
            from framework.common.exceptions import BadRequestError
            raise BadRequestError("租户ID不能为空")

        result = await plugin_config_service.config_plugin(
            session=session,
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            plugin_config=request.plugin_config if request else None,
            runtime_config=request.runtime_config if request else None,
        )

        return ApiResponse.success(data=result.model_dump())
    except Exception as e:
        _logger.exception("配置插件失败")
        from framework.common.exceptions import BadRequestError
        raise BadRequestError(f"配置插件失败: {str(e)}")


@router.post(
    "/{plugin_id}/test",
    summary="测试插件配置连接",
    response_class=ORJSONResponse,
)
async def test_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    测试插件配置连接

    场景：用户测试已配置的插件是否能正常连接
    WHEN 请求 POST /ai/console/v1/plugins/installations/{plugin_id}/test
    THEN 返回连接测试结果

    Args:
        plugin_id: 插件 ID
        session: 数据库会话

    Returns:
        PluginTestResponse
    """
    try:
        tenant_id = get_tenant_id()
        if not tenant_id:
            from framework.common.exceptions import BadRequestError
            raise BadRequestError("租户ID不能为空")

        result = await plugin_config_service.test_plugin(
            session=session,
            tenant_id=tenant_id,
            plugin_id=plugin_id,
        )

        return ApiResponse.success(data=result.model_dump())
    except Exception as e:
        _logger.exception("测试插件配置失败")
        from framework.common.exceptions import BadRequestError
        raise BadRequestError(f"测试插件配置失败: {str(e)}")


@router.post(
    "/{plugin_id}/start",
    summary="启动插件",
    response_class=ORJSONResponse,
)
async def start_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    启动插件

    场景：用户启动状态为 INACTIVE 的插件
    WHEN 请求 POST /ai/console/v1/plugins/installations/{plugin_id}/start
    THEN 创建插件进程，更新状态为 ACTIVE，返回进程信息

    Args:
        plugin_id: 插件 ID
        session: 数据库会话

    Returns:
        PluginStartResponse
    """
    try:
        tenant_id = get_tenant_id()
        if not tenant_id:
            from framework.common.exceptions import BadRequestError
            raise BadRequestError("租户ID不能为空")

        result = await plugin_config_service.start_plugin(
            session=session,
            tenant_id=tenant_id,
            plugin_id=plugin_id,
        )

        return ApiResponse.success(data=result.model_dump())
    except Exception as e:
        _logger.exception("启动插件失败")
        from framework.common.exceptions import BadRequestError
        raise BadRequestError(f"启动插件失败: {str(e)}")


@router.post(
    "/{plugin_id}/stop",
    summary="停止插件",
    response_class=ORJSONResponse,
)
async def stop_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    停止插件

    场景：用户停止状态为 ACTIVE 的插件
    WHEN 请求 POST /ai/console/v1/plugins/installations/{plugin_id}/stop
    THEN 终止插件进程，更新状态为 INACTIVE

    Args:
        plugin_id: 插件 ID
        session: 数据库会话

    Returns:
        PluginStopResponse
    """
    try:
        tenant_id = get_tenant_id()
        if not tenant_id:
            from framework.common.exceptions import BadRequestError
            raise BadRequestError("租户ID不能为空")

        result = await plugin_config_service.stop_plugin(
            session=session,
            tenant_id=tenant_id,
            plugin_id=plugin_id,
        )

        return ApiResponse.success(data=result.model_dump())
    except Exception as e:
        _logger.exception("停止插件失败")
        from framework.common.exceptions import BadRequestError
        raise BadRequestError(f"停止插件失败: {str(e)}")
