"""
模块同步事件处理器

监听 Tenant 模块发布的领域事件，同步模块定义层数据到租户实例层。
"""

import json
import logging
from typing import Any

from framework.cache.redis_util import RedisUtil
from framework.database.dependencies import get_listener_session
from framework.events.base import EventStream
from framework.tenant.context import TenantContext
from iam.services.module_sync_service import module_sync_service

_logger = logging.getLogger(__name__)


class BaseEventHandler:
    """事件处理器基类"""

    stream: str = ""
    """监听的 Redis Stream 名称"""

    group: str = "iam_module_sync_group"
    """消费者组名称"""

    consumer: str = "iam_consumer"
    """消费者名称"""

    async def handle(self, message: dict[str, Any]) -> None:
        """
        处理事件消息

        Args:
            message: 消息内容
        """
        raise NotImplementedError


class ModuleAssignedHandler(BaseEventHandler):
    """
    模块分配事件处理器

    监听 ModuleAssigned 事件，为租户创建模块的菜单、权限、角色。
    """

    stream = EventStream.MODULE_ASSIGNED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块分配事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            tenant_id = data.get("tenant_id")
            module_id = data.get("module_id")

            if not tenant_id or not module_id:
                _logger.warning(f"ModuleAssigned 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleAssigned 事件: tenant_id={tenant_id}, module_id={module_id}")

            # 设置租户上下文
            TenantContext.set_tenant_id(tenant_id)

            # 获取模块编码
            from tenant.models import Module
            from sqlalchemy import select

            async with get_listener_session() as session:
                module_stmt = select(Module).where(Module.id == module_id)
                module_result = await session.execute(module_stmt)
                module = module_result.scalar_one_or_none()

                if not module:
                    _logger.warning(f"模块不存在: {module_id}")
                    return

                # 同步模块数据
                await module_sync_service.sync_module_assigned(
                    session, tenant_id, module_id, module.code
                )

            _logger.info(f"ModuleAssigned 事件处理完成: tenant_id={tenant_id}, module_id={module_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleAssigned 事件失败: {e}")
            raise


class ModuleUnassignedHandler(BaseEventHandler):
    """
    模块取消分配事件处理器

    监听 ModuleUnassigned 事件，删除租户的模块菜单、权限、角色。
    """

    stream = EventStream.MODULE_UNASSIGNED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块取消分配事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            tenant_id = data.get("tenant_id")
            module_id = data.get("module_id")

            if not tenant_id or not module_id:
                _logger.warning(f"ModuleUnassigned 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleUnassigned 事件: tenant_id={tenant_id}, module_id={module_id}")

            # 设置租户上下文
            TenantContext.set_tenant_id(tenant_id)

            async with get_listener_session() as session:
                # 同步删除模块数据
                await module_sync_service.sync_module_unassigned(session, tenant_id, module_id)

            _logger.info(f"ModuleUnassigned 事件处理完成: tenant_id={tenant_id}, module_id={module_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleUnassigned 事件失败: {e}")
            raise


class ModuleMenuCreatedHandler(BaseEventHandler):
    """模块菜单创建事件处理器"""

    stream = EventStream.MODULE_MENU_CREATED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块菜单创建事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_menu_id = data.get("module_menu_id")
            module_id = data.get("module_id")

            if not module_menu_id or not module_id:
                _logger.warning(f"ModuleMenuCreated 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleMenuCreated 事件: module_menu_id={module_menu_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_menu_created(
                    session, module_menu_id, module_id
                )

            _logger.info(f"ModuleMenuCreated 事件处理完成: module_menu_id={module_menu_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleMenuCreated 事件失败: {e}")
            raise


class ModuleMenuUpdatedHandler(BaseEventHandler):
    """模块菜单更新事件处理器"""

    stream = EventStream.MODULE_MENU_UPDATED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块菜单更新事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_menu_id = data.get("module_menu_id")
            module_id = data.get("module_id")

            if not module_menu_id or not module_id:
                _logger.warning(f"ModuleMenuUpdated 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleMenuUpdated 事件: module_menu_id={module_menu_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_menu_updated(
                    session, module_menu_id, module_id
                )

            _logger.info(f"ModuleMenuUpdated 事件处理完成: module_menu_id={module_menu_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleMenuUpdated 事件失败: {e}")
            raise


class ModuleMenuDeletedHandler(BaseEventHandler):
    """模块菜单删除事件处理器"""

    stream = EventStream.MODULE_MENU_DELETED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块菜单删除事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_id = data.get("module_id")
            menu_code = data.get("menu_code")

            if not module_id or not menu_code:
                _logger.warning(f"ModuleMenuDeleted 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleMenuDeleted 事件: menu_code={menu_code}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_menu_deleted(
                    session, module_id, menu_code
                )

            _logger.info(f"ModuleMenuDeleted 事件处理完成: menu_code={menu_code}")

        except Exception as e:
            _logger.exception(f"处理 ModuleMenuDeleted 事件失败: {e}")
            raise


class ModulePermissionCreatedHandler(BaseEventHandler):
    """模块权限创建事件处理器"""

    stream = EventStream.MODULE_PERMISSION_CREATED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块权限创建事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_permission_id = data.get("module_permission_id")
            module_id = data.get("module_id")

            if not module_permission_id or not module_id:
                _logger.warning(f"ModulePermissionCreated 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModulePermissionCreated 事件: module_permission_id={module_permission_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_permission_created(
                    session, module_permission_id, module_id
                )

            _logger.info(f"ModulePermissionCreated 事件处理完成: module_permission_id={module_permission_id}")

        except Exception as e:
            _logger.exception(f"处理 ModulePermissionCreated 事件失败: {e}")
            raise


class ModulePermissionUpdatedHandler(BaseEventHandler):
    """模块权限更新事件处理器"""

    stream = EventStream.MODULE_PERMISSION_UPDATED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块权限更新事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_permission_id = data.get("module_permission_id")
            module_id = data.get("module_id")

            if not module_permission_id or not module_id:
                _logger.warning(f"ModulePermissionUpdated 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModulePermissionUpdated 事件: module_permission_id={module_permission_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_permission_updated(
                    session, module_permission_id, module_id
                )

            _logger.info(f"ModulePermissionUpdated 事件处理完成: module_permission_id={module_permission_id}")

        except Exception as e:
            _logger.exception(f"处理 ModulePermissionUpdated 事件失败: {e}")
            raise


class ModulePermissionDeletedHandler(BaseEventHandler):
    """模块权限删除事件处理器"""

    stream = EventStream.MODULE_PERMISSION_DELETED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块权限删除事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_id = data.get("module_id")
            permission_code = data.get("permission_code")

            if not module_id or not permission_code:
                _logger.warning(f"ModulePermissionDeleted 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModulePermissionDeleted 事件: permission_code={permission_code}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_permission_deleted(
                    session, module_id, permission_code
                )

            _logger.info(f"ModulePermissionDeleted 事件处理完成: permission_code={permission_code}")

        except Exception as e:
            _logger.exception(f"处理 ModulePermissionDeleted 事件失败: {e}")
            raise


class ModuleRoleCreatedHandler(BaseEventHandler):
    """模块角色创建事件处理器"""

    stream = EventStream.MODULE_ROLE_CREATED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块角色创建事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_role_id = data.get("module_role_id")
            module_id = data.get("module_id")

            if not module_role_id or not module_id:
                _logger.warning(f"ModuleRoleCreated 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleRoleCreated 事件: module_role_id={module_role_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_role_created(
                    session, module_role_id, module_id
                )

            _logger.info(f"ModuleRoleCreated 事件处理完成: module_role_id={module_role_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleRoleCreated 事件失败: {e}")
            raise


class ModuleRoleUpdatedHandler(BaseEventHandler):
    """模块角色更新事件处理器"""

    stream = EventStream.MODULE_ROLE_UPDATED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块角色更新事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_role_id = data.get("module_role_id")
            module_id = data.get("module_id")

            if not module_role_id or not module_id:
                _logger.warning(f"ModuleRoleUpdated 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleRoleUpdated 事件: module_role_id={module_role_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_role_updated(
                    session, module_role_id, module_id
                )

            _logger.info(f"ModuleRoleUpdated 事件处理完成: module_role_id={module_role_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleRoleUpdated 事件失败: {e}")
            raise


class ModuleRoleDeletedHandler(BaseEventHandler):
    """模块角色删除事件处理器"""

    stream = EventStream.MODULE_ROLE_DELETED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块角色删除事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_id = data.get("module_id")
            role_code = data.get("role_code")

            if not module_id or not role_code:
                _logger.warning(f"ModuleRoleDeleted 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleRoleDeleted 事件: role_code={role_code}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_role_deleted(
                    session, module_id, role_code
                )

            _logger.info(f"ModuleRoleDeleted 事件处理完成: role_code={role_code}")

        except Exception as e:
            _logger.exception(f"处理 ModuleRoleDeleted 事件失败: {e}")
            raise


class ModuleRolePermissionChangedHandler(BaseEventHandler):
    """模块角色权限变更事件处理器"""

    stream = EventStream.MODULE_ROLE_PERMISSION_CHANGED

    async def handle(self, message: dict[str, Any]) -> None:
        """处理模块角色权限变更事件"""
        try:
            data = json.loads(message.get("data", "{}"))
            module_role_id = data.get("module_role_id")
            module_id = data.get("module_id")

            if not module_role_id or not module_id:
                _logger.warning(f"ModuleRolePermissionChanged 事件缺少必要字段: {data}")
                return

            _logger.info(f"处理 ModuleRolePermissionChanged 事件: module_role_id={module_role_id}")

            async with get_listener_session() as session:
                await module_sync_service.sync_module_role_permission_changed(
                    session, module_role_id, module_id
                )

            _logger.info(f"ModuleRolePermissionChanged 事件处理完成: module_role_id={module_role_id}")

        except Exception as e:
            _logger.exception(f"处理 ModuleRolePermissionChanged 事件失败: {e}")
            raise
