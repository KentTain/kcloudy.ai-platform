"""
管理员认证中间件

为管理后台提供独立的超级管理员认证体系。
"""

import secrets
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from framework.common.response import ApiResponse
from framework.utils.crypto import verify_password
from tenant.models import (
    ModuleMenu,
    ModuleMenuPermission,
    ModulePermission,
    ModuleRole,
    ModuleRolePermission,
    TenantAdmin,
)

if TYPE_CHECKING:
    from starlette.types import ASGIApp

_logger = logger.bind(name=__name__)

# 管理后台路径前缀（模块优先路由：/tenant/admin/*）
ADMIN_PATH_PREFIX = "/tenant/admin/"

# Token 存储简化版（生产环境应使用 Redis）
_admin_tokens: dict[str, dict] = {}
# Token 过期时间（小时）
TOKEN_EXPIRE_HOURS = 24


def generate_token() -> str:
    """生成访问令牌"""
    return secrets.token_urlsafe(32)


class AdminAuthService:
    """管理员认证服务"""

    @staticmethod
    async def login(
        session: AsyncSession, username: str, password: str
    ) -> tuple[str, TenantAdmin, list[str]] | None:
        """
        管理员登录

        场景：管理员登录
        WHEN 超级管理员使用正确的用户名和密码登录
        THEN 返回管理员 Token
        """
        stmt = select(TenantAdmin).where(
            TenantAdmin.username == username, TenantAdmin.is_active == True
        )
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            return None

        if not verify_password(password, admin.password):
            return None

        # 查询角色权限
        from tenant.services.module import ModuleService

        tenant_module = await ModuleService.get_by_code(session, "tenant")
        permissions = await AdminAuthService._get_role_permissions(
            session, tenant_module, admin.role
        )

        # 生成 Token
        token = generate_token()
        _admin_tokens[token] = {
            "admin_id": admin.id,
            "username": admin.username,
            "is_default": admin.is_default,
            "role": admin.role,
            "permissions": permissions,
            "expires_at": datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        }

        return token, admin, permissions

    @staticmethod
    async def _get_role_permissions(
        session: AsyncSession, module, role_code: str
    ) -> list[str]:
        """
        查询角色拥有的权限码列表

        通过 role → module_roles → module_role_permissions → module_permissions 链路查询。

        Args:
            session: 数据库会话
            module: 模块对象（可为 None）
            role_code: 角色编码

        Returns:
            权限码列表
        """
        if not module or not role_code:
            return []

        # 1. 查询模块角色
        role_stmt = select(ModuleRole).where(
            ModuleRole.code == role_code,
            ModuleRole.module_id == module.id,
        )
        role_result = await session.execute(role_stmt)
        module_role = role_result.scalar_one_or_none()

        if not module_role:
            return []

        # 2. 查询角色权限关联
        rp_stmt = select(ModuleRolePermission).where(
            ModuleRolePermission.module_role_id == module_role.id
        )
        rp_result = await session.execute(rp_stmt)
        role_permissions = rp_result.scalars().all()

        if not role_permissions:
            return []

        # 3. 查询权限码
        perm_ids = [rp.module_permission_id for rp in role_permissions]
        perm_stmt = select(ModulePermission.code).where(
            ModulePermission.id.in_(perm_ids)
        )
        perm_result = await session.execute(perm_stmt)
        return [row[0] for row in perm_result.all()]

    @staticmethod
    async def get_admin_info(session: AsyncSession, admin_id: str) -> dict | None:
        """
        获取管理员完整信息（角色、权限、菜单树）

        根据 admin_id 查询 TenantAdmin，然后：
        1. 获取角色编码 admin.role
        2. 获取权限码列表（同 login 逻辑）
        3. 获取可访问的菜单树（只包含有权限的可见菜单）

        Args:
            session: 数据库会话
            admin_id: 管理员 ID

        Returns:
            dict 或 None（管理员不存在）
        """
        stmt = select(TenantAdmin).where(TenantAdmin.id == admin_id)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            return None

        role = admin.role

        # 获取权限
        from tenant.services.module import ModuleService

        tenant_module = await ModuleService.get_by_code(session, "tenant")
        permissions = await AdminAuthService._get_role_permissions(
            session, tenant_module, role
        )

        # 获取菜单树
        menus = await AdminAuthService._get_admin_menus(
            session, tenant_module, permissions
        )

        return {
            "id": admin.id,
            "username": admin.username,
            "role": role,
            "permissions": permissions,
            "is_default": admin.is_default,
            "is_active": admin.is_active,
            "created_at": admin.created_at,
            "menus": menus,
        }

    @staticmethod
    async def _get_admin_menus(
        session: AsyncSession,
        module,
        permissions: list[str] | None = None,
    ) -> list[dict]:
        """
        获取管理后台菜单树（三级结构，包含不可见菜单用于面包屑导航）

        根据模块对象查询其下的所有菜单，并通过 ModuleMenuPermission
        判断角色是否有权访问。

        Args:
            session: 数据库会话
            module: 模块对象
            permissions: 权限码列表（None 表示不做权限过滤）

        Returns:
            菜单树列表
        """
        if not module:
            return []

        from tenant.services.module import ModuleMenuService

        # 获取该模块的所有菜单（包括不可见菜单，用于面包屑导航）
        all_menus = await ModuleMenuService.list_menus(session, module.id)

        if not all_menus:
            return []

        # 权限过滤
        if permissions is not None:
            # 查询该模块下所有权限 ID -> 权限码映射
            perm_stmt = select(ModulePermission.id, ModulePermission.code).where(
                ModulePermission.module_id == module.id
            )
            perm_result = await session.execute(perm_stmt)
            perm_id_to_code: dict[str, str] = {
                row[0]: row[1] for row in perm_result.all()
            }

            # 查询菜单权限关联
            menu_ids = [m.id for m in all_menus]
            menu_perm_codes: dict[str, list[str]] = {}

            if menu_ids:
                mmp_stmt = select(ModuleMenuPermission).where(
                    ModuleMenuPermission.module_menu_id.in_(menu_ids)
                )
                mmp_result = await session.execute(mmp_stmt)
                for mmp in mmp_result.scalars().all():
                    perm_code = perm_id_to_code.get(mmp.module_permission_id)
                    if perm_code:
                        menu_perm_codes.setdefault(mmp.module_menu_id, []).append(
                            perm_code
                        )

            # 过滤：菜单有关联权限但角色不拥有这些权限，则隐藏
            visible_menu_ids = set()
            for m in all_menus:
                linked_codes = menu_perm_codes.get(m.id, [])
                if not linked_codes:
                    # 菜单没有权限关联，对所有角色可见
                    visible_menu_ids.add(m.id)
                elif any(code in permissions for code in linked_codes):
                    # 菜单有权限关联且角色拥有至少一个权限
                    visible_menu_ids.add(m.id)

            # 包含父菜单（子菜单有权限时，父菜单也需要显示）
            menu_map = {m.id: m for m in all_menus}
            for menu_id in list(visible_menu_ids):
                menu = menu_map.get(menu_id)
                if menu and menu.parent_ids:
                    for parent_id in menu.parent_ids.split(","):
                        parent_id = parent_id.strip()
                        if parent_id and parent_id != "root":
                            visible_menu_ids.add(parent_id)

            # 过滤菜单列表
            filtered_menus = [m for m in all_menus if m.id in visible_menu_ids]
        else:
            filtered_menus = all_menus

        # 使用 build_tree 构建树形结构
        menu_tree = ModuleMenuService.build_tree(filtered_menus)

        # 递归添加 is_visible 字段
        def add_visible_field(node: dict) -> dict:
            node["is_visible"] = node.get("is_visible", True)
            if "children" in node:
                node["children"] = [
                    add_visible_field(child) for child in node["children"]
                ]
            return node

        menu_tree = [add_visible_field(m) for m in menu_tree]

        # 构建模块级根菜单
        module_menu = {
            "id": module.id,
            "module_id": module.id,
            "parent_id": None,
            "code": module.code,
            "name": module.name,
            "path": "",
            "icon": module.icon,
            "tree_sort": 0,
            "tree_level": 0,
            "tree_leaf": False,
            "is_visible": True,
            "children": menu_tree,
        }

        return [module_menu]

    @staticmethod
    def verify_token(token: str) -> dict | None:
        """验证 Token"""
        if token not in _admin_tokens:
            return None

        token_data = _admin_tokens[token]
        if datetime.now() > token_data["expires_at"]:
            del _admin_tokens[token]
            return None

        return token_data

    @staticmethod
    def logout(token: str) -> bool:
        """登出"""
        if token in _admin_tokens:
            del _admin_tokens[token]
            return True
        return False


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    管理员认证中间件

    场景：非管理员访问被拒绝
    WHEN 普通用户尝试访问管理后台 API
    THEN 返回 HTTP 403 错误

    场景：无 Token 访问被拒绝
    WHEN 未携带 Token 访问管理后台 API
    THEN 返回 HTTP 401 错误
    """

    # 路径前缀到模块权限的映射
    PATH_MODULE_MAP: dict[str, str] = {
        "/tenant/admin/v1/tenants": "tenant:tenant",
        "/tenant/admin/v1/modules": "tenant:module",
        "/tenant/admin/v1/resources": "tenant:resource",
        "/tenant/admin/v1/resource-configs": "tenant:resource",
        "/tenant/admin/v1/plugin-definitions": "tenant:plugin",
        "/tenant/admin/v1/plugin-installations": "tenant:plugin-installation",
        "/tenant/admin/v1/marketplaces": "tenant:marketplace",
    }

    def __init__(self, app: "ASGIApp"):
        super().__init__(app)
        self._security = HTTPBearer(auto_error=False)

    async def dispatch(self, request: "Request", call_next: Callable):
        """处理请求"""
        # 检查是否是管理后台路径
        if not request.url.path.startswith(ADMIN_PATH_PREFIX):
            return await call_next(request)

        # 登录接口跳过认证，标记为已认证
        if request.url.path == "/tenant/admin/v1/auth/login":
            request.state.authenticated = True
            return await call_next(request)

        try:
            # 提取 Token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                _logger.warning(f"[AdminAuth] 未提供认证令牌: path={request.url.path}")
                return self._error_response(401, "未提供认证令牌")

            token = auth_header.replace("Bearer ", "")

            # 调试日志
            _logger.info(f"[AdminAuth] 验证 Token: path={request.url.path}, token={token[:20]}...")
            _logger.info(f"[AdminAuth] 当前存储的 Token 数量: {len(_admin_tokens)}")

            # 验证 Token
            token_data = AdminAuthService.verify_token(token)
            if not token_data:
                _logger.warning(f"[AdminAuth] Token 验证失败: token={token[:20]}..., stored_tokens={list(_admin_tokens.keys())[:3]}")
                return self._error_response(401, "无效或过期的令牌")

            _logger.info(f"[AdminAuth] Token 验证成功: admin={token_data.get('username')}")

            # 注入管理员信息到请求状态
            request.state.admin = token_data
            request.state.authenticated = True  # 标记已认证，供后续中间件识别

            # API 级权限校验（Task 6.1），带路由级作用域
            if request.method in ("POST", "PUT", "DELETE"):
                permissions = token_data.get("permissions", [])
                if not self._check_api_permission(
                    request.method, request.url.path, permissions
                ):
                    return self._error_response(403, "权限不足")

            return await call_next(request)

        except Exception as e:
            _logger.exception("管理员认证中间件处理异常")
            return self._error_response(500, str(e))

    def _check_api_permission(
        self, method: str, path: str, permissions: list[str]
    ) -> bool:
        """
        检查 API 权限（路由级作用域）

        针对非 GET 请求进行权限校验：
        - 通配权限 *:*:* 允许所有操作
        - 根据请求路径确定所需的模块权限前缀
        - POST/PUT 需要对应模块的 :write 权限
        - DELETE 需要对应模块的 :delete 权限
        - 空权限列表拒绝所有非 GET 请求
        - 无法映射到模块的路径，根据方法放行

        Args:
            method: HTTP 方法
            path: 请求路径
            permissions: 权限码列表

        Returns:
            bool: 是否有权限
        """
        if not permissions:
            return False

        # 通配权限
        if "*:*:*" in permissions:
            return True

        if method not in ("POST", "PUT", "DELETE"):
            return True  # GET requests pass through

        # 根据请求路径确定所需的模块权限前缀
        required_module = None
        for prefix, module_perm in self.PATH_MODULE_MAP.items():
            if path.startswith(prefix):
                required_module = module_perm
                break

        if required_module is None:
            # 无法映射到模块的路径，根据方法放行
            return True

        suffix = ":write" if method in ("POST", "PUT", "DELETE") else ":read"
        required_perm = f"{required_module}{suffix}"

        return required_perm in permissions

    def _error_response(self, status_code: int, message: str) -> ApiResponse:
        """生成错误响应"""
        return ApiResponse.fail(code=status_code, msg=message)


# 依赖注入：获取当前管理员
async def get_current_admin(request: Request) -> dict:
    """获取当前登录的管理员"""
    admin = getattr(request.state, "admin", None)
    if not admin:
        raise HTTPException(status_code=401, detail="未认证")
    return admin


def require_admin_permission(permission_code: str):
    """
    管理员权限检查依赖工厂

    创建一个检查指定权限的 FastAPI 依赖。

    Args:
        permission_code: 需要的权限编码

    Returns:
        依赖函数

    Usage:
        @router.get("/tenants")
        async def list_tenants(
            _: None = Depends(require_admin_permission("tenant:tenant:read")),
            session: AsyncSession = Depends(get_db_session),
        ):
            ...
    """

    async def check_permission(request: Request) -> None:
        """检查管理员权限"""
        admin = getattr(request.state, "admin", None)
        if not admin:
            raise HTTPException(status_code=401, detail="未认证")

        permissions = admin.get("permissions", [])

        # 通配权限
        if "*:*:*" in permissions:
            return

        # 精确匹配
        if permission_code in permissions:
            return

        # 模块通配：tenant:*:*
        parts = permission_code.split(":")
        if len(parts) == 3:
            module, resource, action = parts
            if f"{module}:*:*" in permissions:
                return
            if f"{module}:{resource}:*" in permissions:
                return

        raise HTTPException(status_code=403, detail="权限不足")

    return check_permission
