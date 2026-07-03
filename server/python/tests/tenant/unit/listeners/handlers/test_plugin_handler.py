"""
插件安装失败事件处理器单元测试

验证 PluginInstallationFailedHandler 的幂等保护逻辑：
- PENDING → FAILED：合法转换，提交事务
- ACTIVE/INACTIVE/FAILED → 保持原状态：幂等跳过，不覆盖
- 安装记录不存在：记录警告，不抛异常
- 缺少必要字段：提前返回
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tenant.listeners.handlers.plugin_handler import (
    PluginInstallationFailedHandler,
)


def _make_message(tenant_id: str = "tenant-1", plugin_id: str = "test/plugin") -> dict:
    return {
        "data": json.dumps(
            {
                "tenant_id": tenant_id,
                "plugin_id": plugin_id,
                "error_message": "模拟安装失败",
            }
        )
    }


def _patch_session(session: MagicMock):
    """构造 get_listener_session 异步上下文管理器 mock"""

    @asynccontextmanager
    async def _fake_session():
        yield session

    return _fake_session


def _make_installation(status: str) -> MagicMock:
    inst = MagicMock()
    inst.status = status
    return inst


class TestPluginInstallationFailedHandlerIdempotency:
    """幂等保护测试：仅 PENDING → FAILED"""

    @pytest.mark.asyncio
    async def test_pending_installation_marked_failed(self):
        """PENDING 状态的安装记录应被标记为 FAILED 并提交"""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        installation = _make_installation("PENDING")

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session",
            _patch_session(mock_session),
        ), patch(
            "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
            new_callable=AsyncMock,
            return_value=installation,
        ):
            handler = PluginInstallationFailedHandler()
            await handler.handle(_make_message())

        assert installation.status == "FAILED"
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_active_installation_not_overwritten(self):
        """ACTIVE 状态的安装记录不应被覆盖为 FAILED（幂等保护）"""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        installation = _make_installation("ACTIVE")

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session",
            _patch_session(mock_session),
        ), patch(
            "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
            new_callable=AsyncMock,
            return_value=installation,
        ):
            handler = PluginInstallationFailedHandler()
            await handler.handle(_make_message())

        # 幂等：ACTIVE 保持不变，不提交
        assert installation.status == "ACTIVE"
        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_failed_installation_not_re_marked(self):
        """已是 FAILED 状态的记录不应重复处理（幂等保护）"""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        installation = _make_installation("FAILED")

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session",
            _patch_session(mock_session),
        ), patch(
            "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
            new_callable=AsyncMock,
            return_value=installation,
        ):
            handler = PluginInstallationFailedHandler()
            await handler.handle(_make_message())

        assert installation.status == "FAILED"
        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_inactive_installation_not_overwritten(self):
        """INACTIVE 状态的安装记录不应被覆盖为 FAILED"""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        installation = _make_installation("INACTIVE")

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session",
            _patch_session(mock_session),
        ), patch(
            "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
            new_callable=AsyncMock,
            return_value=installation,
        ):
            handler = PluginInstallationFailedHandler()
            await handler.handle(_make_message())

        assert installation.status == "INACTIVE"
        mock_session.commit.assert_not_awaited()


class TestPluginInstallationFailedHandlerEdgeCases:
    """边界场景测试"""

    @pytest.mark.asyncio
    async def test_installation_not_found_logs_warning(self):
        """安装记录不存在时应记录警告，不抛异常"""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session",
            _patch_session(mock_session),
        ), patch(
            "tenant.models.plugin_installation.TenantPluginInstallation.first_by_fields",
            new_callable=AsyncMock,
            return_value=None,
        ):
            handler = PluginInstallationFailedHandler()
            # 不应抛异常
            await handler.handle(_make_message())

        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_tenant_id_returns_early(self):
        """缺少 tenant_id 时应提前返回，不访问数据库"""
        message = {
            "data": json.dumps({"plugin_id": "test/plugin"}),  # 缺少 tenant_id
        }

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session"
        ) as mock_get_session:
            handler = PluginInstallationFailedHandler()
            await handler.handle(message)

        # 缺少必要字段时不应进入 session 上下文
        mock_get_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_plugin_id_returns_early(self):
        """缺少 plugin_id 时应提前返回"""
        message = {
            "data": json.dumps({"tenant_id": "tenant-1"}),  # 缺少 plugin_id
        }

        with patch(
            "tenant.listeners.handlers.plugin_handler.get_listener_session"
        ) as mock_get_session:
            handler = PluginInstallationFailedHandler()
            await handler.handle(message)

        mock_get_session.assert_not_called()
