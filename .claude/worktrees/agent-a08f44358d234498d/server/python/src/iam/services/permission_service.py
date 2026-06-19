"""
权限管理服务

提供权限查询和检查功能。
"""

from collections import defaultdict
from typing import Any

from loguru import logger
from sqlalchemy import func, select

from iam.models import Permission, Role, RolePermission, UserRole
from framework.cache.redis_util import RedisUtil
from framework.database.core.engine import async_session

_logger = logger.bind(name=__name__)

# 权限缓存配置
PERMISSION_CACHE_PREFIX = "user_permissions:"
PERMISSION_CACHE_TTL = 300  # 5 分钟


class PermissionService:
    """权限管理服务"""

    @staticmethod
    async def get_all_permissions() -> list[Permission]:
        """获取所有权限"""
        async with async_session() as session:
            stmt = select(Permission).order_by(Permission.resource, Permission.action)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_permissions_by_resource(resource: str) -> list[Permission]:
        """获取指定资源的权限"""
        async with async_session() as session:
            stmt = (
                select(Permission)
                .where(Permission.resource == resource)
                .order_by(Permission.action)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_permissions_grouped() -> dict[str, list[Permission]]:
        """按资源分组获取权限"""
        permissions = await PermissionService.get_all_permissions()
        grouped: dict[str, list[Permission]] = defaultdict(list)
        for perm in permissions:
            grouped[perm.resource].append(perm)
        return dict(grouped)


class PermissionCheckService:
    """权限检查服务"""

    @staticmethod
    async def get_user_permissions(user_id: str, use_cache: bool = True) -> list[str]:
        """
        获取用户的所有权限编码

        Args:
            user_id: 用户 ID
            use_cache: 是否使用缓存

        Returns:
            list[str]: 权限编码列表
        """
        # 尝试从缓存获取
        if use_cache and RedisUtil.is_initialized():
            try:
                cache_key = f"{PERMISSION_CACHE_PREFIX}{user_id}"
                cached = await RedisUtil.get(cache_key)
                if cached:
                    import json
                    return json.loads(cached)
            except (RuntimeError, Exception) as e:
                _logger.debug(f"Redis 缓存读取失败，降级到数据库查询: {e}")

        # 从数据库查询
        async with async_session() as session:
            stmt = (
                select(Permission.code)
                .distinct()
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .join(UserRole, RolePermission.role_id == UserRole.role_id)
                .where(UserRole.user_id == user_id)
            )
            result = await session.execute(stmt)
            permissions = [row for row in result.scalars().all()]

        # 写入缓存
        if use_cache and RedisUtil.is_initialized():
            try:
                cache_key = f"{PERMISSION_CACHE_PREFIX}{user_id}"
                import json
                await RedisUtil.set(
                    cache_key,
                    json.dumps(permissions),
                    ttl=PERMISSION_CACHE_TTL,
                )
            except (RuntimeError, Exception) as e:
                _logger.debug(f"Redis 缓存写入失败，跳过缓存: {e}")

        return permissions

    @staticmethod
    async def has_permission(user_id: str, permission_code: str) -> bool:
        """
        检查用户是否拥有指定权限

        支持通配符匹配：
        - user:* 匹配所有 user: 前缀的权限
        - * 匹配所有权限

        Args:
            user_id: 用户 ID
            permission_code: 权限编码

        Returns:
            bool: 是否拥有权限
        """
        permissions = await PermissionCheckService.get_user_permissions(user_id)

        # 检查完全匹配
        if permission_code in permissions:
            return True

        # 检查通配符
        if "*" in permissions:
            return True

        # 检查资源级通配符
        if ":" in permission_code:
            resource = permission_code.split(":")[0]
            if f"{resource}:*" in permissions:
                return True

        return False

    @staticmethod
    async def has_any_permission(user_id: str, permission_codes: list[str]) -> bool:
        """
        检查用户是否拥有任一权限

        Args:
            user_id: 用户 ID
            permission_codes: 权限编码列表

        Returns:
            bool: 是否拥有任一权限
        """
        for code in permission_codes:
            if await PermissionCheckService.has_permission(user_id, code):
                return True
        return False

    @staticmethod
    async def has_all_permissions(user_id: str, permission_codes: list[str]) -> bool:
        """
        检查用户是否拥有所有权限

        Args:
            user_id: 用户 ID
            permission_codes: 权限编码列表

        Returns:
            bool: 是否拥有所有权限
        """
        for code in permission_codes:
            if not await PermissionCheckService.has_permission(user_id, code):
                return False
        return True

    @staticmethod
    async def invalidate_user_permission_cache(user_id: str) -> None:
        """
        使用户权限缓存失效

        在用户角色变更、角色权限变更时调用。

        Args:
            user_id: 用户 ID
        """
        if not RedisUtil.is_initialized():
            return
        try:
            cache_key = f"{PERMISSION_CACHE_PREFIX}{user_id}"
            await RedisUtil.delete(cache_key)
            _logger.debug(f"权限缓存已清除: {user_id}")
        except (RuntimeError, Exception) as e:
            _logger.debug(f"权限缓存清除失败: {e}")

    @staticmethod
    async def invalidate_tenant_permission_cache(tenant_id: str) -> None:
        """
        使租户内所有用户的权限缓存失效

        在租户角色变更时调用。

        Args:
            tenant_id: 租户 ID
        """
        if not RedisUtil.is_initialized():
            return
        # 查找租户内所有用户
        from iam.models import UserTenant
        async with async_session() as session:
            stmt = select(UserTenant.user_id).where(UserTenant.tenant_id == tenant_id)
            result = await session.execute(stmt)
            user_ids = [row for row in result.scalars().all()]

        # 批量清除缓存
        for user_id in user_ids:
            await PermissionCheckService.invalidate_user_permission_cache(user_id)

        _logger.info(f"租户权限缓存已清除: {tenant_id} ({len(user_ids)} users)")


# 服务单例
permission_service = PermissionService()
permission_check_service = PermissionCheckService()
