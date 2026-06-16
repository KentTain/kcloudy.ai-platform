"""
管理后台系统设置控制器
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse

from tenant.middlewares.admin_auth_middleware import get_current_admin
from iam.schemas.admin.system_setting import (
    SystemSettingCreate,
    SystemSettingPaginatedListResponse,
    SystemSettingResponse,
    SystemSettingUpdate,
    SystemSettingPaginatedQuery,
)
from iam.services.system_setting_service import system_setting_service

router = APIRouter()


def Success(data=None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


def build_setting_response(setting) -> SystemSettingResponse:
    """构建设置响应对象"""
    return SystemSettingResponse.model_validate(setting)


@router.get("")
async def list_settings(
    query: SystemSettingPaginatedQuery = Depends(),
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    查询系统设置列表

    场景：管理员列出配置
    WHEN 管理员发送 GET /admin/v1/system-settings
    THEN 返回当前租户的所有配置列表
    """
    tenant_id = "platform"  # 系统设置为平台级配置
    settings, total = await system_setting_service.list_settings(
        tenant_id=tenant_id,
        page=query.page,
        page_size=query.page_size,
        keyword=query.keyword,
    )

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": SystemSettingPaginatedListResponse(
                items=[build_setting_response(s) for s in settings],
                total=total,
                page=query.page,
                page_size=query.page_size,
            ).model_dump(),
        }
    )


@router.post("")
async def create_setting(
    data: SystemSettingCreate,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    创建系统设置

    场景：管理员创建配置
    WHEN 管理员发送 POST /admin/v1/system-settings，body 包含 name、code 和 attributes
    THEN 创建成功返回 201，响应包含完整的配置和属性值

    场景：创建重复编号配置
    WHEN 管理员尝试创建已存在 code 的配置
    THEN 返回 HTTP 400 错误
    """
    tenant_id = "platform"  # 系统设置为平台级配置

    existing = await system_setting_service.get_setting_by_code(tenant_id, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="设置编号已存在")

    setting = await system_setting_service.create_setting(
        tenant_id=tenant_id,
        code=data.code,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        application_id=data.application_id,
        application_name=data.application_name,
        can_edit=data.can_edit,
        is_require=data.is_require,
        index=data.index,
        attributes=[attr.model_dump() for attr in data.attributes],
    )

    return ORJSONResponse(
        content=Success(build_setting_response(setting).model_dump())
    )


@router.get("/{setting_id}")
async def get_setting(
    setting_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    查询系统设置详情

    场景：管理员查询配置详情
    WHEN 管理员发送 GET /admin/v1/system-settings/{id}
    THEN 返回配置详细信息

    场景：查询不存在的配置
    WHEN 管理员请求 GET /admin/v1/system-settings/nonexistent
    THEN 返回 HTTP 404 错误
    """
    setting = await system_setting_service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    return ORJSONResponse(
        content=Success(build_setting_response(setting).model_dump())
    )


@router.put("/{setting_id}")
async def update_setting(
    setting_id: str,
    data: SystemSettingUpdate,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    更新系统设置

    场景：管理员更新配置
    WHEN 管理员发送 PUT /admin/v1/system-settings/{id} 并提供更新数据
    THEN 更新配置信息并返回更新后的数据

    场景：更新配置时同步更新属性值
    WHEN 调用 update_setting 更新配置的 attributes 列表
    THEN 已有属性值更新、新增属性值创建、多余属性值删除
    """
    setting = await system_setting_service.update_setting(
        setting_id=setting_id,
        code=data.code,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        application_id=data.application_id,
        application_name=data.application_name,
        can_edit=data.can_edit,
        is_require=data.is_require,
        index=data.index,
        attributes=[attr.model_dump() for attr in data.attributes] if data.attributes else None,
    )

    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    return ORJSONResponse(
        content=Success(build_setting_response(setting).model_dump())
    )


@router.delete("/{setting_id}")
async def delete_setting(
    setting_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    删除系统设置

    场景：管理员删除配置
    WHEN 管理员发送 DELETE /admin/v1/system-settings/{id}
    THEN 删除配置（级联删除属性值）
    """
    success = await system_setting_service.delete_setting(setting_id)
    if not success:
        raise HTTPException(status_code=404, detail="设置不存在")

    return ORJSONResponse(content=Success())
