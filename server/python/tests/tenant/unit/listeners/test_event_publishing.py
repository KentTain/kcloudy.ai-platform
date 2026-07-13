"""
事件发布单元测试
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from framework.events.base import EventStream
from framework.events.domain_events import (
    ModuleAssigned,
    ModuleMenuCreated,
    ModuleMenuDeleted,
    ModuleMenuUpdated,
    ModulePermissionCreated,
    ModulePermissionDeleted,
    ModulePermissionUpdated,
    ModuleRoleCreated,
    ModuleRoleDeleted,
    ModuleRolePermissionChanged,
    ModuleRoleUpdated,
    ModuleUnassigned,
)


class TestDomainEvent:
    """领域事件基类测试"""

    def test_event_has_unique_id(self):
        """事件有唯一 ID"""
        event1 = ModuleAssigned(tenant_id="t1", module_id="m1")
        event2 = ModuleAssigned(tenant_id="t1", module_id="m1")

        assert event1.event_id != event2.event_id

    def test_event_type_is_class_name(self):
        """事件类型是类名"""
        event = ModuleAssigned(tenant_id="t1", module_id="m1")

        assert event.event_type == "ModuleAssigned"

    def test_event_has_timestamp(self):
        """事件有时间戳"""
        event = ModuleAssigned(tenant_id="t1", module_id="m1")

        assert isinstance(event.timestamp, datetime)

    def test_to_dict(self):
        """转换为字典"""
        event = ModuleAssigned(tenant_id="tenant-1", module_id="module-1")

        data = event.to_dict()

        assert data["tenant_id"] == "tenant-1"
        assert data["module_id"] == "module-1"
        assert data["event_type"] == "ModuleAssigned"
        assert "event_id" in data
        assert "timestamp" in data

    def test_to_json(self):
        """转换为 JSON"""
        event = ModuleAssigned(tenant_id="tenant-1", module_id="module-1")

        json_str = event.to_json()

        assert isinstance(json_str, str)
        assert "tenant-1" in json_str
        assert "module-1" in json_str


class TestModuleAssignedEvent:
    """模块分配事件测试"""

    def test_event_data(self):
        """事件数据正确"""
        event = ModuleAssigned(
            tenant_id="tenant-1",
            module_id="module-1",
        )

        assert event.tenant_id == "tenant-1"
        assert event.module_id == "module-1"

    def test_get_stream_name(self):
        """获取事件流名称"""
        stream = ModuleAssigned.get_stream_name()

        assert stream == EventStream.MODULE_ASSIGNED


class TestModuleUnassignedEvent:
    """模块取消分配事件测试"""

    def test_event_data(self):
        """事件数据正确"""
        event = ModuleUnassigned(
            tenant_id="tenant-1",
            module_id="module-1",
        )

        assert event.tenant_id == "tenant-1"
        assert event.module_id == "module-1"

    def test_get_stream_name(self):
        """获取事件流名称"""
        stream = ModuleUnassigned.get_stream_name()

        assert stream == EventStream.MODULE_UNASSIGNED


class TestModuleMenuEvents:
    """模块菜单事件测试"""

    def test_menu_created_event(self):
        """菜单创建事件"""
        event = ModuleMenuCreated(
            module_menu_id="menu-1",
            module_id="module-1",
        )

        assert event.module_menu_id == "menu-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_MENU_CREATED

    def test_menu_updated_event(self):
        """菜单更新事件"""
        event = ModuleMenuUpdated(
            module_menu_id="menu-1",
            module_id="module-1",
        )

        assert event.module_menu_id == "menu-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_MENU_UPDATED

    def test_menu_deleted_event(self):
        """菜单删除事件"""
        event = ModuleMenuDeleted(
            module_id="module-1",
            menu_code="dashboard",
        )

        assert event.module_id == "module-1"
        assert event.menu_code == "dashboard"
        assert event.get_stream_name() == EventStream.MODULE_MENU_DELETED


class TestModulePermissionEvents:
    """模块权限事件测试"""

    def test_permission_created_event(self):
        """权限创建事件"""
        event = ModulePermissionCreated(
            module_permission_id="perm-1",
            module_id="module-1",
        )

        assert event.module_permission_id == "perm-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_PERMISSION_CREATED

    def test_permission_updated_event(self):
        """权限更新事件"""
        event = ModulePermissionUpdated(
            module_permission_id="perm-1",
            module_id="module-1",
        )

        assert event.module_permission_id == "perm-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_PERMISSION_UPDATED

    def test_permission_deleted_event(self):
        """权限删除事件"""
        event = ModulePermissionDeleted(
            module_id="module-1",
            permission_code="user:read",
        )

        assert event.module_id == "module-1"
        assert event.permission_code == "user:read"
        assert event.get_stream_name() == EventStream.MODULE_PERMISSION_DELETED


class TestModuleRoleEvents:
    """模块角色事件测试"""

    def test_role_created_event(self):
        """角色创建事件"""
        event = ModuleRoleCreated(
            module_role_id="role-1",
            module_id="module-1",
        )

        assert event.module_role_id == "role-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_ROLE_CREATED

    def test_role_updated_event(self):
        """角色更新事件"""
        event = ModuleRoleUpdated(
            module_role_id="role-1",
            module_id="module-1",
        )

        assert event.module_role_id == "role-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_ROLE_UPDATED

    def test_role_deleted_event(self):
        """角色删除事件"""
        event = ModuleRoleDeleted(
            module_id="module-1",
            role_code="admin",
        )

        assert event.module_id == "module-1"
        assert event.role_code == "admin"
        assert event.get_stream_name() == EventStream.MODULE_ROLE_DELETED


class TestModuleRolePermissionChangedEvent:
    """模块角色权限变更事件测试"""

    def test_event_data(self):
        """事件数据正确"""
        event = ModuleRolePermissionChanged(
            module_role_id="role-1",
            module_id="module-1",
        )

        assert event.module_role_id == "role-1"
        assert event.module_id == "module-1"
        assert event.get_stream_name() == EventStream.MODULE_ROLE_PERMISSION_CHANGED


class TestEventPublisher:
    """事件发布器测试"""

    @pytest.mark.asyncio
    async def test_publish_module_assigned_event(self):
        """发布模块分配事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = ModuleAssigned(tenant_id="tenant-1", module_id="module-1")
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.MODULE_ASSIGNED

    @pytest.mark.asyncio
    async def test_publish_module_menu_created_event(self):
        """发布模块菜单创建事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = ModuleMenuCreated(module_menu_id="menu-1", module_id="module-1")
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.MODULE_MENU_CREATED

    @pytest.mark.asyncio
    async def test_publish_module_permission_created_event(self):
        """发布模块权限创建事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = ModulePermissionCreated(
                module_permission_id="perm-1", module_id="module-1"
            )
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.MODULE_PERMISSION_CREATED

    @pytest.mark.asyncio
    async def test_publish_module_role_created_event(self):
        """发布模块角色创建事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = ModuleRoleCreated(module_role_id="role-1", module_id="module-1")
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.MODULE_ROLE_CREATED

    @pytest.mark.asyncio
    async def test_publish_module_role_permission_changed_event(self):
        """发布模块角色权限变更事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = ModuleRolePermissionChanged(
                module_role_id="role-1", module_id="module-1"
            )
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.MODULE_ROLE_PERMISSION_CHANGED
