"""
插件事件发布单元测试

测试插件安装失败、卸载失败等事件的发布逻辑。
"""

from unittest.mock import AsyncMock, patch

import pytest

from framework.events.base import DomainEvent, EventStream
from framework.events.domain_events import (
    PluginInstallationFailed,
    PluginUninstallFailed,
)


class TestPluginInstallationFailedEvent:
    """插件安装失败事件测试"""

    def test_event_data(self):
        """事件数据正确"""
        event = PluginInstallationFailed(
            tenant_id="tenant-001",
            plugin_id="author/plugin-name",
            error_message="配置创建失败",
        )

        assert event.tenant_id == "tenant-001"
        assert event.plugin_id == "author/plugin-name"
        assert event.error_message == "配置创建失败"

    def test_event_has_unique_id(self):
        """事件有唯一 ID"""
        event1 = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error1"
        )
        event2 = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error1"
        )

        assert event1.event_id != event2.event_id

    def test_event_type_is_class_name(self):
        """事件类型是类名"""
        event = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error"
        )

        assert event.event_type == "PluginInstallationFailed"

    def test_get_stream_name(self):
        """获取事件流名称"""
        stream = PluginInstallationFailed.get_stream_name()

        assert stream == EventStream.PLUGIN_INSTALLATION_FAILED

    def test_event_to_dict(self):
        """转换为字典"""
        event = PluginInstallationFailed(
            tenant_id="tenant-001",
            plugin_id="author/plugin-name",
            error_message="配置创建失败",
        )

        data = event.to_dict()

        assert data["tenant_id"] == "tenant-001"
        assert data["plugin_id"] == "author/plugin-name"
        assert data["error_message"] == "配置创建失败"
        assert data["event_type"] == "PluginInstallationFailed"
        assert "event_id" in data
        assert "timestamp" in data

    def test_event_to_json(self):
        """转换为 JSON"""
        event = PluginInstallationFailed(
            tenant_id="tenant-001",
            plugin_id="author/plugin-name",
            error_message="配置创建失败",
        )

        json_str = event.to_json()

        assert isinstance(json_str, str)
        assert "tenant-001" in json_str
        assert "author/plugin-name" in json_str
        assert "配置创建失败" in json_str


class TestPluginUninstallFailedEvent:
    """插件卸载失败事件测试"""

    def test_event_data(self):
        """事件数据正确"""
        event = PluginUninstallFailed(
            tenant_id="tenant-001",
            plugin_id="author/plugin-name",
            error_message="数据删除失败",
        )

        assert event.tenant_id == "tenant-001"
        assert event.plugin_id == "author/plugin-name"
        assert event.error_message == "数据删除失败"

    def test_event_has_unique_id(self):
        """事件有唯一 ID"""
        event1 = PluginUninstallFailed(
            tenant_id="t1", plugin_id="p1", error_message="error1"
        )
        event2 = PluginUninstallFailed(
            tenant_id="t1", plugin_id="p1", error_message="error1"
        )

        assert event1.event_id != event2.event_id

    def test_event_type_is_class_name(self):
        """事件类型是类名"""
        event = PluginUninstallFailed(
            tenant_id="t1", plugin_id="p1", error_message="error"
        )

        assert event.event_type == "PluginUninstallFailed"

    def test_get_stream_name(self):
        """获取事件流名称"""
        stream = PluginUninstallFailed.get_stream_name()

        assert stream == EventStream.PLUGIN_UNINSTALL_FAILED

    def test_event_to_dict(self):
        """转换为字典"""
        event = PluginUninstallFailed(
            tenant_id="tenant-001",
            plugin_id="author/plugin-name",
            error_message="数据删除失败",
        )

        data = event.to_dict()

        assert data["tenant_id"] == "tenant-001"
        assert data["plugin_id"] == "author/plugin-name"
        assert data["error_message"] == "数据删除失败"
        assert data["event_type"] == "PluginUninstallFailed"
        assert "event_id" in data
        assert "timestamp" in data


class TestPluginEventPublishing:
    """插件事件发布测试"""

    @pytest.mark.asyncio
    async def test_publish_installation_failed_event(self):
        """测试发布安装失败事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = PluginInstallationFailed(
                tenant_id="tenant-001",
                plugin_id="author/plugin-name",
                error_message="配置创建失败",
            )
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.PLUGIN_INSTALLATION_FAILED

    @pytest.mark.asyncio
    async def test_publish_uninstall_failed_event(self):
        """测试发布卸载失败事件"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = PluginUninstallFailed(
                tenant_id="tenant-001",
                plugin_id="author/plugin-name",
                error_message="数据删除失败",
            )
            await event_publisher.publish(event)

        mock_xadd.assert_called_once()
        call_args = mock_xadd.call_args
        assert call_args[0][0] == EventStream.PLUGIN_UNINSTALL_FAILED

    @pytest.mark.asyncio
    async def test_publish_with_retry_success_on_first_attempt(self):
        """测试带重试的事件发布（第一次成功）"""
        from framework.events import event_publisher

        with patch("framework.events.publisher.RedisUtil.xadd") as mock_xadd:
            mock_xadd.return_value = "1234567890-0"

            event = PluginInstallationFailed(
                tenant_id="tenant-001",
                plugin_id="author/plugin-name",
                error_message="配置创建失败",
            )

            # 模拟发布成功（带重试）
            success = False
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await event_publisher.publish(event)
                    success = True
                    break
                except Exception:
                    continue

            assert success is True
            mock_xadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_with_retry_success_on_second_attempt(self):
        """测试带重试的事件发布（第二次成功）"""
        from framework.events import event_publisher

        call_count = 0

        def mock_xadd_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("第一次失败")
            return "1234567890-0"

        with patch(
            "framework.events.publisher.RedisUtil.xadd",
            side_effect=mock_xadd_side_effect,
        ):
            event = PluginInstallationFailed(
                tenant_id="tenant-001",
                plugin_id="author/plugin-name",
                error_message="配置创建失败",
            )

            # 模拟发布成功（带重试）
            success = False
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await event_publisher.publish(event)
                    success = True
                    break
                except Exception:
                    continue

            assert success is True
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_publish_with_retry_all_attempts_failed(self):
        """测试带重试的事件发布（所有尝试都失败）"""
        from framework.events import event_publisher

        call_count = 0

        def mock_xadd_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("持续失败")

        with patch(
            "framework.events.publisher.RedisUtil.xadd",
            side_effect=mock_xadd_side_effect,
        ):
            event = PluginInstallationFailed(
                tenant_id="tenant-001",
                plugin_id="author/plugin-name",
                error_message="配置创建失败",
            )

            # 模拟发布失败（带重试）
            success = False
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await event_publisher.publish(event)
                    success = True
                    break
                except Exception:
                    continue

            assert success is False
            assert call_count == 3


class TestDomainEventBase:
    """领域事件基类测试"""

    def test_event_inherits_from_domain_event(self):
        """插件事件继承自 DomainEvent"""
        event = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error"
        )

        assert isinstance(event, DomainEvent)

    def test_event_has_timestamp(self):
        """事件有时间戳"""
        event = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error"
        )

        assert hasattr(event, "timestamp")
        assert event.timestamp is not None

    def test_event_equality(self):
        """事件相等性比较（基于 event_id）"""
        event1 = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error"
        )
        event2 = PluginInstallationFailed(
            tenant_id="t1", plugin_id="p1", error_message="error"
        )

        # 不同的事件实例有不同的 event_id
        assert event1 != event2

        # 同一个事件实例与自身相等
        assert event1 == event1
