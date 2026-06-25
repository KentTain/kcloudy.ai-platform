"""
AI 模块控制台控制器 - 插件安装管理

提供插件安装、卸载、运行时管理、统计等用户端接口。
"""

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas import (
    GetPluginConfigSuccessRespModel,
    GetPluginStatisticsSuccessRespModel,
    GetRuntimeStateListSuccessRespModel,
    GetRuntimeStateSuccessRespModel,
    StartPluginSuccessRespModel,
    StopPluginSuccessRespModel,
    UninstallPluginSuccessRespModel,
    UpdatePluginConfigRequest,
    UpdatePluginConfigSuccessRespModel,
)
from ai.services import plugin_management_service
from framework.common.exceptions import BadRequestError
from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from iam.dependencies import require_permission

_logger = logger.bind(name=__name__)

router = APIRouter(tags=["控制台-插件安装管理"])


# ==================== 卸载插件 ====================


@router.delete(
    "/{plugin_id:path}",
    summary="卸载插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件卸载成功",
            "model": UninstallPluginSuccessRespModel,
        },
    },
)
async def uninstall_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:delete")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    卸载插件

    场景：用户卸载插件
    WHEN 请求 DELETE /console/v1/plugins/installations/{plugin_id}
    THEN 停止插件进程、清理配置数据、递减引用计数
    """
    try:
        result = await plugin_management_service.uninstall_plugin(session, plugin_id)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"插件卸载失败: {str(e)}")
    except Exception as e:
        _logger.exception("插件卸载失败")
        raise BadRequestError(f"插件卸载失败: {str(e)}")


# ==================== 运行时管理 ====================


@router.post(
    "/{plugin_id:path}/start",
    summary="启动插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件启动成功",
            "model": StartPluginSuccessRespModel,
        },
    },
)
async def start_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    启动插件

    场景：用户启动状态为 INACTIVE 的插件
    WHEN 请求 POST /console/v1/plugins/installations/{plugin_id}/start
    THEN 创建插件进程，更新状态为 ACTIVE，返回进程信息
    """
    try:
        result = await plugin_management_service.start_plugin_with_response(session, plugin_id)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"插件启动失败: {str(e)}")
    except Exception as e:
        _logger.exception("插件启动失败")
        raise BadRequestError(f"插件启动失败: {str(e)}")


@router.post(
    "/{plugin_id:path}/stop",
    summary="停止插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件停止成功",
            "model": StopPluginSuccessRespModel,
        },
    },
)
async def stop_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    停止插件

    场景：用户停止状态为 ACTIVE 的插件
    WHEN 请求 POST /console/v1/plugins/installations/{plugin_id}/stop
    THEN 终止插件进程，更新状态为 INACTIVE
    """
    try:
        result = await plugin_management_service.stop_plugin_with_response(session, plugin_id)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"插件停止失败: {str(e)}")
    except Exception as e:
        _logger.exception("插件停止失败")
        raise BadRequestError(f"插件停止失败: {str(e)}")


@router.get(
    "/{plugin_id:path}/config",
    summary="获取插件配置",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "获取成功",
            "model": GetPluginConfigSuccessRespModel,
        },
    },
)
async def get_plugin_config(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件配置

    场景：用户查看插件配置
    WHEN 请求 GET /console/v1/plugins/installations/{plugin_id}/config
    THEN 返回插件能力配置和运行时配置
    """
    try:
        result = await plugin_management_service.get_plugin_config(session, plugin_id)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"获取插件配置失败: {str(e)}")
    except Exception as e:
        _logger.exception("获取插件配置失败")
        raise BadRequestError(f"获取插件配置失败: {str(e)}")


@router.patch(
    "/{plugin_id:path}/config",
    summary="更新插件配置",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "更新成功",
            "model": UpdatePluginConfigSuccessRespModel,
        },
    },
)
async def update_plugin_config(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:write")),
    request: UpdatePluginConfigRequest = Body(..., description="配置更新请求"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新插件配置

    场景：用户更新插件运行时配置
    WHEN 请求 PATCH /console/v1/plugins/installations/{plugin_id}/config
    THEN 更新运行时配置并返回更新后的配置
    """
    try:
        result = await plugin_management_service.update_plugin_config(session, plugin_id, request)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"更新插件配置失败: {str(e)}")
    except Exception as e:
        _logger.exception("更新插件配置失败")
        raise BadRequestError(f"更新插件配置失败: {str(e)}")


@router.get(
    "/{plugin_id:path}/runtime-state",
    summary="获取插件运行时状态",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "获取成功",
            "model": GetRuntimeStateSuccessRespModel,
        },
    },
)
async def get_runtime_state(
    plugin_id: str = Path(..., description="插件ID"),
    _perm: None = Depends(require_permission("ai:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件运行时状态

    场景：用户查看单个插件的运行时状态
    WHEN 请求 GET /console/v1/plugins/installations/{plugin_id}/runtime-state
    THEN 返回进程信息、统计信息、健康状态
    """
    try:
        result = await plugin_management_service.get_runtime_state(session, plugin_id)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"获取运行时状态失败: {str(e)}")
    except Exception as e:
        _logger.exception("获取运行时状态失败")
        raise BadRequestError(f"获取运行时状态失败: {str(e)}")


# ==================== 统计仪表板 ====================


@router.get(
    "/statistics",
    summary="获取插件使用统计",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "获取成功",
            "model": GetPluginStatisticsSuccessRespModel,
        },
    },
)
async def get_statistics(
    _perm: None = Depends(require_permission("ai:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件使用统计

    场景：用户查看租户的插件使用统计数据
    WHEN 请求 GET /console/v1/plugins/statistics
    THEN 返回状态统计、使用统计、运行时统计
    """
    try:
        result = await plugin_management_service.get_statistics(session)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"获取统计数据失败: {str(e)}")
    except Exception as e:
        _logger.exception("获取统计数据失败")
        raise BadRequestError(f"获取统计数据失败: {str(e)}")
