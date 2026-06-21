"""
管理后台模块定义控制器

包含模块、模块菜单、模块权限、模块角色的 CRUD API。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from tenant.middlewares.admin_auth_middleware import get_current_admin
from tenant.schemas.admin.module import (
    ModuleCreate,
    ModuleMenuCreate,
    ModuleMenuListResponse,
    ModuleMenuPermissionUpdateRequest,
    ModuleMenuTreeResponse,
    ModuleMenuUpdate,
    ModulePermissionCreate,
    ModulePermissionResponse,
    ModulePermissionUpdate,
    ModuleResponse,
    ModuleRoleCreate,
    ModuleRolePermissionUpdateRequest,
    ModuleRoleResponse,
    ModuleRoleUpdate,
    ModuleUpdate,
)
from tenant.services import (
    ModuleMenuPermissionService,
    ModuleMenuService,
    ModulePermissionService,
    ModuleRoleService,
    ModuleService,
)

router = APIRouter()


def build_module_vo(module) -> ModuleResponse:
    """构建模块响应对象"""
    return ModuleResponse(
        id=module.id,
        code=module.code,
        name=module.name,
        description=module.description,
        icon=module.icon,
        version=module.version,
        is_active=module.is_active,
        is_need=module.is_need,
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


def build_menu_vo(menu, children: list = None) -> ModuleMenuTreeResponse:
    """构建菜单响应对象"""
    return ModuleMenuTreeResponse(
        id=menu.id,
        module_id=menu.module_id,
        parent_id=menu.parent_id,
        code=menu.code,
        name=menu.name,
        path=menu.path,
        icon=menu.icon,
        tree_sort=menu.tree_sort,
        tree_level=menu.tree_level,
        tree_leaf=menu.tree_leaf,
        is_visible=menu.is_visible,
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=children or [],
    )


def build_permission_vo(perm) -> ModulePermissionResponse:
    """构建权限响应对象"""
    return ModulePermissionResponse(
        id=perm.id,
        module_id=perm.module_id,
        code=perm.code,
        name=perm.name,
        resource=perm.resource,
        action=perm.action,
        description=perm.description,
        created_at=perm.created_at,
        updated_at=perm.updated_at,
    )


def build_role_vo(role, permissions: list = None) -> ModuleRoleResponse:
    """构建角色响应对象"""
    return ModuleRoleResponse(
        id=role.id,
        module_id=role.module_id,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=[build_permission_vo(p) for p in (permissions or [])],
    )


# =============================================================================
# 模块管理 API
# =============================================================================


@router.get("/modules")
async def list_modules(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    is_active: bool | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询模块列表

    场景：查询模块列表
    WHEN 管理员请求 GET /admin/v1/modules
    THEN 返回所有模块列表（分页）

    场景：搜索模块
    WHEN 管理员请求 GET /admin/v1/modules?keyword=iam
    THEN 返回名称或编码包含 "iam" 的模块列表
    """
    modules, total = await ModuleService.list_modules(
        session,
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active,
    )

    return ApiResponse.paginated(
        data=[build_module_vo(m) for m in modules],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/modules")
async def create_module(
    data: ModuleCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建模块

    场景：创建模块
    WHEN 管理员请求 POST /admin/v1/modules 并提供编码、名称
    THEN 创建新模块并返回模块信息

    场景：创建重复编码模块
    WHEN 管理员尝试创建已存在编码的模块
    THEN 返回 HTTP 400 错误，消息为 "模块编码已存在"
    """
    # 检查编码是否已存在
    existing = await ModuleService.get_by_code(session, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="模块编码已存在")

    module = await ModuleService.create(
        session,
        code=data.code,
        name=data.name,
        description=data.description,
        icon=data.icon,
        version=data.version,
        is_active=data.is_active,
        is_need=data.is_need,
    )

    return ApiResponse.success(data=build_module_vo(module).model_dump())


@router.get("/modules/{module_id}")
async def get_module(
    module_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询模块详情

    场景：查询模块详情
    WHEN 管理员请求 GET /admin/v1/modules/{id}
    THEN 返回模块详细信息

    场景：查询不存在的模块
    WHEN 管理员请求 GET /admin/v1/modules/nonexistent
    THEN 返回 HTTP 404 错误
    """
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    return ApiResponse.success(data=build_module_vo(module).model_dump())


@router.put("/modules/{module_id}")
async def update_module(
    module_id: str,
    data: ModuleUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新模块

    场景：更新模块
    WHEN 管理员请求 PUT /admin/v1/modules/{id} 并提供更新数据
    THEN 更新模块信息并返回更新后的数据
    """
    module = await ModuleService.update(
        session,
        module_id=module_id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        version=data.version,
        is_active=data.is_active,
        is_need=data.is_need,
    )

    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    return ApiResponse.success(data=build_module_vo(module).model_dump())


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除模块

    场景：删除模块
    WHEN 管理员请求 DELETE /admin/v1/modules/{id}
    THEN 删除模块

    场景：删除已分配给租户的模块
    WHEN 管理员尝试删除已被租户分配的模块
    THEN 返回 HTTP 400 错误，消息为 "模块已被租户分配，无法删除"
    """
    try:
        success = await ModuleService.delete(session, module_id)
        if not success:
            raise HTTPException(status_code=404, detail="模块不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse.success(data=success)


# =============================================================================
# 模块菜单 API
# =============================================================================


@router.get("/modules/{module_id}/menus")
async def list_module_menus(
    module_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询模块菜单列表（树形）

    场景：查询模块菜单
    WHEN 管理员请求 GET /admin/v1/modules/{id}/menus
    THEN 返回模块的菜单树形结构
    """
    # 检查模块是否存在
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    menus = await ModuleMenuService.list_menus(session, module_id)
    tree = ModuleMenuService.build_tree(menus)

    return ApiResponse.success(data=ModuleMenuListResponse(items=tree).model_dump())


@router.post("/modules/{module_id}/menus")
async def create_module_menu(
    module_id: str,
    data: ModuleMenuCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建模块菜单

    场景：创建模块菜单
    WHEN 管理员请求 POST /admin/v1/modules/{id}/menus 并提供菜单信息
    THEN 创建菜单并返回菜单信息

    场景：创建重复编码菜单
    WHEN 管理员尝试创建已存在编码的菜单
    THEN 返回 HTTP 400 错误，消息为 "菜单编码已存在"
    """
    # 检查模块是否存在
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    # 检查编码是否已存在
    existing = await ModuleMenuService.get_by_code(session, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="菜单编码已存在")

    # 检查父菜单是否存在
    if data.parent_id:
        parent = await ModuleMenuService.get_by_id(session, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="父菜单不存在")
        if parent.module_id != module_id:
            raise HTTPException(status_code=400, detail="父菜单不属于该模块")

    menu = await ModuleMenuService.create(
        session,
        module_id=module_id,
        code=data.code,
        name=data.name,
        path=data.path,
        parent_id=data.parent_id,
        icon=data.icon,
        tree_sort=data.tree_sort,
        is_visible=data.is_visible,
    )

    return ApiResponse.success(data=build_menu_vo(menu).model_dump())


@router.put("/modules/{module_id}/menus/{menu_id}")
async def update_module_menu(
    module_id: str,
    menu_id: str,
    data: ModuleMenuUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新模块菜单

    场景：更新模块菜单
    WHEN 管理员请求 PUT /admin/v1/modules/{id}/menus/{menuId} 并提供更新数据
    THEN 更新菜单信息并返回更新后的数据
    """
    # 检查菜单是否存在且属于该模块
    menu = await ModuleMenuService.get_by_id(session, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    if menu.module_id != module_id:
        raise HTTPException(status_code=400, detail="菜单不属于该模块")

    try:
        menu = await ModuleMenuService.update(
            session,
            menu_id=menu_id,
            name=data.name,
            path=data.path,
            parent_id=data.parent_id,
            icon=data.icon,
            tree_sort=data.tree_sort,
            is_visible=data.is_visible,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse.success(data=build_menu_vo(menu).model_dump())


@router.delete("/modules/{module_id}/menus/{menu_id}")
async def delete_module_menu(
    module_id: str,
    menu_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除模块菜单

    场景：删除模块菜单
    WHEN 管理员请求 DELETE /admin/v1/modules/{id}/menus/{menuId}
    THEN 删除菜单

    场景：删除有子菜单的菜单
    WHEN 管理员尝试删除有子菜单的菜单
    THEN 返回 HTTP 400 错误，消息为 "菜单有子菜单，无法删除"
    """
    # 检查菜单是否存在且属于该模块
    menu = await ModuleMenuService.get_by_id(session, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    if menu.module_id != module_id:
        raise HTTPException(status_code=400, detail="菜单不属于该模块")

    try:
        success = await ModuleMenuService.delete(session, menu_id)
        if not success:
            raise HTTPException(status_code=404, detail="菜单不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse.success(data=success)


# =============================================================================
# 模块权限 API
# =============================================================================


@router.get("/modules/{module_id}/permissions")
async def list_module_permissions(
    module_id: str,
    page: int = 1,
    page_size: int = 100,
    resource: str | None = None,
    action: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询模块权限列表

    场景：查询模块权限
    WHEN 管理员请求 GET /admin/v1/modules/{id}/permissions
    THEN 返回模块的权限列表
    """
    # 检查模块是否存在
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    permissions, total = await ModulePermissionService.list_permissions(
        session,
        module_id=module_id,
        page=page,
        page_size=page_size,
        resource=resource,
        action=action,
    )

    return ApiResponse.paginated(
        data=[build_permission_vo(p) for p in permissions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/modules/{module_id}/permissions")
async def create_module_permission(
    module_id: str,
    data: ModulePermissionCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建模块权限

    场景：创建模块权限
    WHEN 管理员请求 POST /admin/v1/modules/{id}/permissions 并提供权限信息
    THEN 创建权限并返回权限信息

    场景：创建重复编码权限
    WHEN 管理员尝试创建已存在编码的权限
    THEN 返回 HTTP 400 错误，消息为 "权限编码已存在"
    """
    # 检查模块是否存在
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    # 检查编码是否已存在
    existing = await ModulePermissionService.get_by_code(session, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="权限编码已存在")

    # 验证 action 值
    if data.action not in ("read", "write", "delete"):
        raise HTTPException(status_code=400, detail="操作类型必须是 read/write/delete")

    permission = await ModulePermissionService.create(
        session,
        module_id=module_id,
        code=data.code,
        name=data.name,
        resource=data.resource,
        action=data.action,
        description=data.description,
    )

    return ApiResponse.success(data=build_permission_vo(permission).model_dump())


@router.put("/modules/{module_id}/permissions/{permission_id}")
async def update_module_permission(
    module_id: str,
    permission_id: str,
    data: ModulePermissionUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新模块权限

    场景：更新模块权限
    WHEN 管理员请求 PUT /admin/v1/modules/{id}/permissions/{permId} 并提供更新数据
    THEN 更新权限信息并返回更新后的数据
    """
    # 检查权限是否存在且属于该模块
    permission = await ModulePermissionService.get_by_id(session, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    if permission.module_id != module_id:
        raise HTTPException(status_code=400, detail="权限不属于该模块")

    # 验证 action 值
    if data.action is not None and data.action not in ("read", "write", "delete"):
        raise HTTPException(status_code=400, detail="操作类型必须是 read/write/delete")

    permission = await ModulePermissionService.update(
        session,
        permission_id=permission_id,
        name=data.name,
        resource=data.resource,
        action=data.action,
        description=data.description,
    )

    return ApiResponse.success(data=build_permission_vo(permission).model_dump())


@router.delete("/modules/{module_id}/permissions/{permission_id}")
async def delete_module_permission(
    module_id: str,
    permission_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除模块权限

    场景：删除模块权限
    WHEN 管理员请求 DELETE /admin/v1/modules/{id}/permissions/{permId}
    THEN 删除权限
    """
    # 检查权限是否存在且属于该模块
    permission = await ModulePermissionService.get_by_id(session, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    if permission.module_id != module_id:
        raise HTTPException(status_code=400, detail="权限不属于该模块")

    success = await ModulePermissionService.delete(session, permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="权限不存在")

    return ApiResponse.success(data=success)


# =============================================================================
# 模块角色 API
# =============================================================================


@router.get("/modules/{module_id}/roles")
async def list_module_roles(
    module_id: str,
    page: int = 1,
    page_size: int = 100,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询模块角色列表

    场景：查询模块角色
    WHEN 管理员请求 GET /admin/v1/modules/{id}/roles
    THEN 返回模块的角色列表（包含权限信息）
    """
    # 检查模块是否存在
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    roles, total = await ModuleRoleService.list_roles(
        session,
        module_id=module_id,
        page=page,
        page_size=page_size,
    )

    # 构建响应（包含权限信息）
    role_vos = []
    for role in roles:
        permissions = await ModuleRoleService.get_role_permissions(session, role.id)
        role_vos.append(build_role_vo(role, permissions))

    return ApiResponse.paginated(
        data=role_vos,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/modules/{module_id}/roles")
async def create_module_role(
    module_id: str,
    data: ModuleRoleCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建模块角色

    场景：创建模块角色
    WHEN 管理员请求 POST /admin/v1/modules/{id}/roles 并提供角色信息
    THEN 创建角色并返回角色信息

    场景：创建重复编码角色
    WHEN 管理员尝试创建已存在编码的角色
    THEN 返回 HTTP 400 错误，消息为 "角色编码已存在"
    """
    # 检查模块是否存在
    module = await ModuleService.get_by_id(session, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    # 检查编码是否已存在
    existing = await ModuleRoleService.get_by_code(session, module_id, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="角色编码已存在")

    role = await ModuleRoleService.create(
        session,
        module_id=module_id,
        code=data.code,
        name=data.name,
        description=data.description,
        is_system=data.is_system,
    )

    return ApiResponse.success(data=build_role_vo(role).model_dump())


@router.put("/modules/{module_id}/roles/{role_id}")
async def update_module_role(
    module_id: str,
    role_id: str,
    data: ModuleRoleUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新模块角色

    场景：更新模块角色
    WHEN 管理员请求 PUT /admin/v1/modules/{id}/roles/{roleId} 并提供更新数据
    THEN 更新角色信息并返回更新后的数据

    场景：更新系统内置角色
    WHEN 管理员尝试更新系统内置角色
    THEN 返回 HTTP 400 错误，消息为 "系统内置角色禁止修改"
    """
    # 检查角色是否存在且属于该模块
    role = await ModuleRoleService.get_by_id(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.module_id != module_id:
        raise HTTPException(status_code=400, detail="角色不属于该模块")

    try:
        role = await ModuleRoleService.update(
            session,
            role_id=role_id,
            name=data.name,
            description=data.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    permissions = await ModuleRoleService.get_role_permissions(session, role.id)
    return ApiResponse.success(data=build_role_vo(role, permissions).model_dump())


@router.delete("/modules/{module_id}/roles/{role_id}")
async def delete_module_role(
    module_id: str,
    role_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除模块角色

    场景：删除模块角色
    WHEN 管理员请求 DELETE /admin/v1/modules/{id}/roles/{roleId}
    THEN 删除角色

    场景：删除系统内置角色
    WHEN 管理员尝试删除系统内置角色
    THEN 返回 HTTP 400 错误，消息为 "系统内置角色禁止删除"
    """
    # 检查角色是否存在且属于该模块
    role = await ModuleRoleService.get_by_id(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.module_id != module_id:
        raise HTTPException(status_code=400, detail="角色不属于该模块")

    try:
        success = await ModuleRoleService.delete(session, role_id)
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse.success(data=success)


@router.put("/modules/{module_id}/roles/{role_id}/permissions")
async def update_role_permissions(
    module_id: str,
    role_id: str,
    data: ModuleRolePermissionUpdateRequest,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新角色权限列表（整体替换）

    场景：更新角色权限
    WHEN 管理员请求 PUT /admin/v1/modules/{id}/roles/{roleId}/permissions 并提供权限 ID 列表
    THEN 更新角色权限并返回更新后的权限列表

    场景：更新系统内置角色权限
    WHEN 管理员尝试更新系统内置角色的权限
    THEN 返回 HTTP 400 错误，消息为 "系统内置角色禁止修改权限"
    """
    # 检查角色是否存在且属于该模块
    role = await ModuleRoleService.get_by_id(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.module_id != module_id:
        raise HTTPException(status_code=400, detail="角色不属于该模块")

    try:
        permissions = await ModuleRoleService.update_role_permissions(
            session,
            role_id=role_id,
            permission_ids=data.permission_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse.success(data=build_role_vo(role, permissions).model_dump())


# =============================================================================
# 模块菜单权限 API
# =============================================================================


@router.get("/modules/{module_id}/menus/{menu_id}/permissions")
async def list_menu_permissions(
    module_id: str,
    menu_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取菜单关联的权限列表

    场景：查询菜单权限
    WHEN 管理员请求 GET /admin/v1/modules/{id}/menus/{menuId}/permissions
    THEN 返回菜单关联的权限列表
    """
    # 检查菜单是否存在且属于该模块
    menu = await ModuleMenuService.get_by_id(session, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    if menu.module_id != module_id:
        raise HTTPException(status_code=400, detail="菜单不属于该模块")

    permissions = await ModuleMenuPermissionService.get_menu_permissions(session, menu_id)

    return ApiResponse.success(data=[build_permission_vo(p) for p in permissions])


@router.put("/modules/{module_id}/menus/{menu_id}/permissions")
async def update_menu_permissions(
    module_id: str,
    menu_id: str,
    data: ModuleMenuPermissionUpdateRequest,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新菜单权限列表（整体替换）

    场景：更新菜单权限
    WHEN 管理员请求 PUT /admin/v1/modules/{id}/menus/{menuId}/permissions 并提供权限 ID 列表
    THEN 更新菜单权限并返回更新后的权限列表
    """
    # 检查菜单是否存在且属于该模块
    menu = await ModuleMenuService.get_by_id(session, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    if menu.module_id != module_id:
        raise HTTPException(status_code=400, detail="菜单不属于该模块")

    try:
        permissions = await ModuleMenuPermissionService.update_menu_permissions(
            session,
            menu_id=menu_id,
            permission_ids=data.permission_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse.success(data=[build_permission_vo(p) for p in permissions])
