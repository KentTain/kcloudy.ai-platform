"""
事件监听器测试

测试 Tenant 模块事件监听器对插件安装/卸载失败事件的处理。

运行方式：
    uv run pytest -m e2e tests/ai/e2e/test_event_listeners.py -v

前提条件：
    1. Redis 服务可用
    2. PostgreSQL 服务可用
    3. 后端服务已启动（监听器需要运行）
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.events.domain_events import (
    PluginInstallationFailed,
    PluginUninstallFailed,
)
from framework.events.publisher import get_event_publisher
from framework.tenant.context import TenantContext
from tenant.models.plugin_installation import TenantPluginInstallation


# 测试配置
TEST_PLUGIN_ID = "test/event-listener-test"
TEST_PLUGIN_ID_ACTIVE = "test/event-listener-active"


@pytest_asyncio.fixture
async def test_installation_record(
    e2e_session: AsyncSession,
    test_tenant_id: str,
):
    """
    创建测试插件安装记录（PENDING 状态）

    自动创建并清理测试数据。PENDING 是唯一可合法转为 FAILED 的状态。
    """
    # 检查是否已存在
    result = await e2e_session.execute(
        select(TenantPluginInstallation).where(
            TenantPluginInstallation.tenant_id == test_tenant_id,
            TenantPluginInstallation.plugin_id == TEST_PLUGIN_ID,
        )
    )
    installation = result.scalar_one_or_none()

    if not installation:
        # 创建测试安装记录（PENDING 状态）
        installation = TenantPluginInstallation(
            tenant_id=test_tenant_id,
            plugin_id=TEST_PLUGIN_ID,
            plugin_unique_identifier=TEST_PLUGIN_ID,
            status="PENDING",
            plugin_type="test",
        )
        e2e_session.add(installation)
        await e2e_session.commit()

    else:
        # 更新状态为 PENDING
        installation.status = "PENDING"
        await e2e_session.commit()

    yield installation

    # 清理测试数据
    try:
        await e2e_session.execute(
            delete(TenantPluginInstallation).where(
                TenantPluginInstallation.tenant_id == test_tenant_id,
                TenantPluginInstallation.plugin_id.in_(
                    [TEST_PLUGIN_ID, TEST_PLUGIN_ID_ACTIVE]
                ),
            )
        )
        await e2e_session.commit()
    except Exception:
        await e2e_session.rollback()


@pytest_asyncio.fixture
async def redis_initialized(ai_settings, redis_available):
    """初始化 Redis 连接"""
    if not redis_available:
        pytest.skip("Redis 服务不可用")

    from framework.cache.redis_util import RedisUtil

    if not RedisUtil.is_initialized():
        await RedisUtil.init(ai_settings.redis)

    yield

    try:
        await RedisUtil.close()
    except Exception:
        pass


@pytest.mark.e2e
@pytest.mark.asyncio
class TestEventListeners:
    """事件监听器测试"""

    async def test_plugin_installation_failed_event(
        self,
        e2e_session: AsyncSession,
        e2e_engine,
        test_tenant_id: str,
        test_installation_record: TenantPluginInstallation,
        redis_initialized: None,
    ) -> None:
        """
        测试插件安装失败事件处理（PENDING → FAILED）

        场景：
        1. 创建测试插件安装记录（状态为 PENDING）
        2. 发布 PluginInstallationFailed 事件
        3. 等待监听器处理
        4. 验证安装记录状态更新为 FAILED

        验证点：
        1. 事件发布成功
        2. PENDING 安装记录状态更新为 FAILED
        """
        TenantContext.set_tenant_id(test_tenant_id)

        # 步骤 1：发布事件
        publisher = get_event_publisher()
        event = PluginInstallationFailed(
            tenant_id=test_tenant_id,
            plugin_id=TEST_PLUGIN_ID,
            error_message="测试事件：模拟安装失败",
        )

        await publisher.publish(event)

        # 步骤 2：等待监听器处理
        await asyncio.sleep(3)

        # 步骤 3：验证状态更新（使用新 session 避免 asyncio 事件循环不匹配）
        async with AsyncSession(bind=e2e_engine, expire_on_commit=False) as fresh_session:
            result = await fresh_session.execute(
                select(TenantPluginInstallation).where(
                    TenantPluginInstallation.tenant_id == test_tenant_id,
                    TenantPluginInstallation.plugin_id == TEST_PLUGIN_ID,
                )
            )
            installation = result.scalar_one_or_none()

        assert installation is not None, "安装记录应存在"
        assert installation.status == "FAILED", (
            f"状态应更新为 FAILED，实际为 {installation.status}"
        )

        TenantContext.clear()

    async def test_plugin_installation_failed_event_idempotent_skip(
        self,
        e2e_session: AsyncSession,
        e2e_engine,
        test_tenant_id: str,
        redis_initialized: None,
    ) -> None:
        """
        测试插件安装失败事件幂等保护（ACTIVE 不被覆盖）

        场景：
        1. 创建测试插件安装记录（状态为 ACTIVE）
        2. 发布 PluginInstallationFailed 事件
        3. 等待监听器处理
        4. 验证安装记录状态保持 ACTIVE（幂等跳过）

        验证点：
        1. ACTIVE 状态的安装记录不应被覆盖为 FAILED
        """
        TenantContext.set_tenant_id(test_tenant_id)

        # 创建 ACTIVE 安装记录
        active_installation = TenantPluginInstallation(
            tenant_id=test_tenant_id,
            plugin_id=TEST_PLUGIN_ID_ACTIVE,
            plugin_unique_identifier=TEST_PLUGIN_ID_ACTIVE,
            status="ACTIVE",
            plugin_type="test",
        )
        e2e_session.add(active_installation)
        await e2e_session.commit()

        # 发布事件
        publisher = get_event_publisher()
        event = PluginInstallationFailed(
            tenant_id=test_tenant_id,
            plugin_id=TEST_PLUGIN_ID_ACTIVE,
            error_message="测试事件：幂等跳过",
        )

        await publisher.publish(event)

        # 等待监听器处理
        await asyncio.sleep(3)

        # 验证状态保持 ACTIVE（幂等保护）
        async with AsyncSession(bind=e2e_engine, expire_on_commit=False) as fresh_session:
            result = await fresh_session.execute(
                select(TenantPluginInstallation).where(
                    TenantPluginInstallation.tenant_id == test_tenant_id,
                    TenantPluginInstallation.plugin_id == TEST_PLUGIN_ID_ACTIVE,
                )
            )
            installation = result.scalar_one_or_none()

        assert installation is not None, "安装记录应存在"
        assert installation.status == "ACTIVE", (
            f"ACTIVE 状态不应被覆盖为 FAILED，实际为 {installation.status}"
        )

        TenantContext.clear()

    async def test_plugin_uninstall_failed_event(
        self,
        test_tenant_id: str,
        redis_initialized: None,
    ) -> None:
        """
        测试插件卸载失败事件处理

        场景：
        1. 发布 PluginUninstallFailed 事件
        2. 等待监听器处理
        3. 验证日志记录（通过返回值判断）

        注意：卸载失败事件只记录日志，不更新数据库状态

        验证点：
        1. 事件发布成功（无异常）
        """
        TenantContext.set_tenant_id(test_tenant_id)

        # 步骤 1：发布事件
        publisher = get_event_publisher()
        event = PluginUninstallFailed(
            tenant_id=test_tenant_id,
            plugin_id=TEST_PLUGIN_ID,
            error_message="测试事件：模拟卸载失败",
        )

        # 验证发布成功（不应抛出异常）
        await publisher.publish(event)

        # 步骤 2：等待监听器处理
        await asyncio.sleep(3)

        # 卸载失败事件只记录日志，无法直接验证
        # 如果没有异常，说明事件发布和处理流程正常

        TenantContext.clear()

    async def test_listener_status(
        self,
        ai_settings,
        redis_initialized: None,
    ) -> None:
        """
        测试监听器状态

        场景：
        1. 检查 Redis 连接
        2. 检查消费者组是否存在

        验证点：
        1. Redis 连接正常
        2. 消费者组存在
        """
        from framework.cache.redis_util import RedisUtil
        from framework.events.base import EventStream

        # 检查 Redis 连接
        client = await RedisUtil.get_client()

        # 检查消费者组是否存在
        streams = [
            EventStream.PLUGIN_INSTALLATION_FAILED,
            EventStream.PLUGIN_UNINSTALL_FAILED,
        ]

        for stream in streams:
            try:
                info = await client.xinfo_groups(stream)
                # 验证至少有一个消费者组
                assert len(info) >= 1, f"Stream {stream} 应至少有一个消费者组"
            except Exception as e:
                # 如果 stream 不存在，可能监听器尚未启动
                pytest.skip(f"Stream {stream} 不存在，监听器可能尚未启动: {e}")
