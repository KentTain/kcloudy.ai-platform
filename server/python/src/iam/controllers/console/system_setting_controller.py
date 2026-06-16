"""
用户端系统设置控制器
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse

from iam.schemas.console.system_setting import (
    ConsoleSystemSettingPaginatedListResponse,
    ConsoleSystemSettingPaginatedQuery,
    ConsoleSystemSettingResponse,
)
from iam.services.system_setting_service import system_setting_service

router = APIRouter()


def Success(data=None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


def build_setting_response(setting) -> ConsoleSystemSettingResponse:
    """构建设置响应对象"""
    return ConsoleSystemSettingResponse.model_validate(setting)


@router.get("")
async def list_settings(
    query: ConsoleSystemSettingPaginatedQuery = Depends(),
    tenant_id: str = "default",
) -> ORJSONResponse:
    """
    列出本租户配置

    场景：用户列出配置
    WHEN 用户发送 GET /console/v1/system-settings
    THEN 返回本租户的所有配置列表
    """
    settings, total = await system_setting_service.list_settings(
        tenant_id=tenant_id,
        page=query.page,
        page_size=query.page_size,
        keyword=query.keyword,
    )

    return ORJSONResponse(
        content=Success(
            ConsoleSystemSettingPaginatedListResponse(
                items=[build_setting_response(s) for s in settings],
                total=total,
                page=query.page,
                page_size=query.page_size,
            ).model_dump()
        )
    )


@router.get("/{setting_id}")
async def get_setting(setting_id: str) -> ORJSONResponse:
    """
    获取配置详情

    场景：用户查询配置详情
    WHEN 用户发送 GET /console/v1/system-settings/{id}
    THEN 返回配置详情和属性值列表
    """
    setting = await system_setting_service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    return ORJSONResponse(
        content=Success(build_setting_response(setting).model_dump())
    )


@router.get("/by-code/{code}")
async def get_setting_by_code(code: str, tenant_id: str = "default") -> ORJSONResponse:
    """
    按编号获取配置

    场景：用户按编号查询配置
    WHEN 用户发送 GET /console/v1/system-settings/by-code/SMTP
    THEN 返回本租户 code 为 "SMTP" 的配置详情和属性值列表
    """
    setting = await system_setting_service.get_setting_by_code(tenant_id, code)
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    return ORJSONResponse(
        content=Success(build_setting_response(setting).model_dump())
    )
