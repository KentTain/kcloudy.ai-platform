"""
AI 模块控制台控制器

提供插件列表、详情、凭证管理等用户端接口。
"""


from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas import (
    CreatePluginCredential,
    GetPluginCredentialsSchemaSuccessRespModel,
    GetPluginCredentialSuccessRespModel,
    GetPluginInfoSuccessRespModel,
    GetPluginListSuccessRespModel,
    ListPluginCredentialSuccessRespModel,
    PluginCredentialsSchemaVo,
    SavePluginCredentialSuccessRespModel,
    UpdatePluginCredential,
)
from ai.services import plugin_management_service
from framework.common.exceptions import BadRequestError
from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra

_logger = logger.bind(name=__name__)

router = APIRouter(tags=["控制台-插件"])


@router.get(
    "",
    summary="获取插件列表",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件列表获取成功",
            "model": GetPluginListSuccessRespModel,
        },
    },
)
async def get_plugin_list(
    status: str | None = Query(None, description="插件状态过滤"),
    plugin_id: str | None = Query(None, description="插件id模糊查询"),
    plugin_type: str | None = Query(None, description="插件类型过滤"),
    limit: int = Query(50, ge=1, le=2000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件列表

    场景：用户查询插件列表
    WHEN 请求 GET /console/v1/plugins
    THEN 返回当前租户的所有插件列表
    """
    try:
        result = await plugin_management_service.get_plugin_list(
            session=session,
            status=status,
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            limit=limit,
            offset=offset,
        )
        return Success(data=result.model_dump())
    except Exception as e:
        _logger.exception("获取插件列表失败")
        raise BadRequestError(f"获取插件列表失败: {str(e)}")


@router.get(
    "/{plugin_id:path}",
    summary="获取插件详情",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件详细信息获取成功",
            "model": GetPluginInfoSuccessRespModel,
        },
    },
)
async def get_plugin_detail(
    plugin_id: str = Path(..., description="插件ID"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件详情

    场景：用户查询插件详情
    WHEN 请求 GET /console/v1/plugins/{plugin_id}
    THEN 返回插件详细信息
    """
    try:
        result = await plugin_management_service.get_plugin_info(session, plugin_id)
        return Success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"插件不存在: {str(e)}")
    except Exception as e:
        _logger.exception("获取插件详情失败")
        raise BadRequestError(f"获取插件详情失败: {str(e)}")


@router.get(
    path="/{plugin_id:path}/credentials",
    summary="获取插件凭证列表",
    response_class=ORJSONResponse,
    responses={
        200: {"description": "获取成功", "model": ListPluginCredentialSuccessRespModel},
    },
)
async def list_credentials(
    plugin_id: str = Path(..., description="插件ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    name: str | None = Query(None, description="凭证名称模糊查询"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件凭证列表

    场景：用户查询插件凭证列表
    WHEN 请求 GET /console/v1/plugins/{plugin_id}/credentials
    THEN 返回凭证列表（分页）
    """
    try:
        total, items = await plugin_management_service.list_credentials(
            session=session,
            plugin_id=plugin_id,
            page=page,
            page_size=page_size,
            name=name,
        )
        return SuccessExtra(
            data=[item.model_dump() for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        _logger.exception("获取插件凭证列表失败")
        raise BadRequestError(f"获取插件凭证列表失败: {str(e)}")


@router.get(
    path="/{plugin_id:path}/credentials/{credential_id}",
    summary="获取凭证详情",
    response_class=ORJSONResponse,
    responses={
        200: {"description": "获取成功", "model": GetPluginCredentialSuccessRespModel},
    },
)
async def get_credential_detail(
    plugin_id: str = Path(..., description="插件ID"),
    credential_id: str = Path(..., description="凭证ID"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取凭证详情

    场景：用户查询凭证详情
    WHEN 请求 GET /console/v1/plugins/{plugin_id}/credentials/{credential_id}
    THEN 返回凭证详细信息（含脱敏后的凭证内容）
    """
    try:
        data = await plugin_management_service.get_credential(session, credential_id)
        return Success(data=data.model_dump())
    except Exception as e:
        _logger.exception("获取凭证详情失败")
        raise BadRequestError(f"获取凭证详情失败: {str(e)}")


@router.get(
    path="/{plugin_id:path}/credentials-schema",
    summary="获取插件凭证架构",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "获取工具凭证架构成功",
            "model": GetPluginCredentialsSchemaSuccessRespModel,
        },
    },
)
async def get_plugin_credentials_schema(
    plugin_id: str = Path(..., description="插件ID"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取插件凭证架构

    场景：用户查询插件凭证架构
    WHEN 请求 GET /console/v1/plugins/{plugin_id}/credentials-schema
    THEN 返回凭证架构定义
    """
    try:
        schema = await plugin_management_service.get_plugin_credentials_schema(
            session, plugin_id
        )
        return Success(
            data=[PluginCredentialsSchemaVo.model_validate(cred) for cred in schema]
        )
    except Exception as e:
        _logger.exception("获取插件凭证架构失败")
        raise BadRequestError(f"获取插件凭证架构失败: {str(e)}")


@router.post(
    path="/{plugin_id:path}/credentials",
    summary="创建插件凭证",
    response_class=ORJSONResponse,
    responses={
        200: {"description": "保存成功", "model": SavePluginCredentialSuccessRespModel},
    },
)
async def create_credential(
    plugin_id: str = Path(..., description="插件ID"),
    obj_in: CreatePluginCredential = Body(..., description="创建凭证请求体"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建插件凭证

    场景：用户创建凭证
    WHEN 请求 POST /console/v1/plugins/{plugin_id}/credentials
    THEN 创建凭证并返回结果

    注意：scope 固定为 global
    """
    try:
        data = await plugin_management_service.create_credential(
            session, plugin_id, obj_in
        )
        return Success(data=data.model_dump())
    except Exception as e:
        _logger.exception("创建插件凭证失败")
        raise BadRequestError(f"创建插件凭证失败: {str(e)}")


@router.put(
    path="/{plugin_id:path}/credentials/{credential_id}",
    summary="更新插件凭证",
    response_class=ORJSONResponse,
    responses={
        200: {"description": "保存成功", "model": SavePluginCredentialSuccessRespModel},
    },
)
async def update_credential(
    plugin_id: str = Path(..., description="插件ID"),
    credential_id: str = Path(..., description="凭证ID"),
    obj_in: UpdatePluginCredential = Body(..., description="更新凭证请求体"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新插件凭证

    场景：用户更新凭证
    WHEN 请求 PUT /console/v1/plugins/{plugin_id}/credentials/{credential_id}
    THEN 更新凭证并返回结果
    """
    try:
        data = await plugin_management_service.update_credential(
            session, plugin_id, credential_id, obj_in
        )
        return Success(data=data.model_dump())
    except Exception as e:
        _logger.exception("更新插件凭证失败")
        raise BadRequestError(f"更新插件凭证失败: {str(e)}")


@router.delete(
    path="/{plugin_id:path}/credentials/{credential_id}",
    summary="删除插件凭证",
    response_class=ORJSONResponse,
)
async def delete_credential(
    plugin_id: str = Path(..., description="插件ID"),
    credential_id: str = Path(..., description="凭证ID"),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除插件凭证

    场景：用户删除凭证
    WHEN 请求 DELETE /console/v1/plugins/{plugin_id}/credentials/{credential_id}
    THEN 删除凭证并返回结果
    """
    try:
        await plugin_management_service.delete_credential(session, credential_id)
        return Success(data=True)
    except Exception as e:
        _logger.exception("删除插件凭证失败")
        raise BadRequestError(f"删除插件凭证失败: {str(e)}")
