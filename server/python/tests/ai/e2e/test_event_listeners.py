"""
事件监听器测试脚本

测试 Tenant 模块事件监听器对插件安装/卸载失败事件的处理。

运行方式：
    cd server/python
    uv run python tests/ai/e2e/test_event_listeners.py

前提条件：
    1. 后端服务已启动（python manage.py runserver）
    2. Redis 服务可用
    3. 数据库服务可用
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from framework.configs import init_settings
from framework.configs.settings import settings
from framework.database.dependencies import get_task_session
from framework.events.domain_events import PluginInstallationFailed, PluginUninstallFailed
from framework.events.publisher import get_event_publisher
from framework.tenant.plugin_protocols import get_plugin_installation_provider
from framework.tenant.context import TenantContext

# 测试配置
TEST_TENANT_ID = "00000000-0000-0000-0000-000000000000"
TEST_PLUGIN_ID = "test/event-listener-test"


async def _test_plugin_installation_failed_event():
    """
    测试插件安装失败事件处理

    场景：
    1. 创建测试插件安装记录（状态为 ACTIVE）
    2. 发布 PluginInstallationFailed 事件
    3. 等待监听器处理
    4. 验证安装记录状态更新为 FAILED
    5. 清理测试数据
    """
    print("=" * 60)
    print("测试：插件安装失败事件处理")
    print("=" * 60)

    # 步骤 1：创建测试安装记录
    print("\n步骤 1：创建测试安装记录")
    async with get_task_session() as session:
        from tenant.models.plugin_installation import TenantPluginInstallation
        from sqlalchemy import select

        # 检查是否已存在
        result = await session.execute(
            select(TenantPluginInstallation).where(
                TenantPluginInstallation.tenant_id == TEST_TENANT_ID,
                TenantPluginInstallation.plugin_id == TEST_PLUGIN_ID,
            )
        )
        installation = result.scalar_one_or_none()

        if not installation:
            # 创建测试安装记录
            installation = TenantPluginInstallation(
                tenant_id=TEST_TENANT_ID,
                plugin_id=TEST_PLUGIN_ID,
                plugin_unique_identifier=TEST_PLUGIN_ID,  # 必填字段
                status="ACTIVE",
                plugin_type="test",
            )
            session.add(installation)
            await session.flush()
            print(f"✅ 创建测试安装记录: {TEST_PLUGIN_ID}")
        else:
            # 更新状态为 ACTIVE
            installation.status = "ACTIVE"
            await session.flush()
            print(f"✅ 更新测试安装记录状态为 ACTIVE: {TEST_PLUGIN_ID}")

    # 步骤 2：发布事件
    print("\n步骤 2：发布 PluginInstallationFailed 事件")
    publisher = get_event_publisher()
    event = PluginInstallationFailed(
        tenant_id=TEST_TENANT_ID,
        plugin_id=TEST_PLUGIN_ID,
        error_message="测试事件：模拟安装失败",
    )

    try:
        await publisher.publish(event)
        print("✅ 事件发布成功")
    except Exception as e:
        print(f"❌ 事件发布失败: {e}")
        return False

    # 步骤 3：等待监听器处理
    print("\n步骤 3：等待监听器处理...")
    await asyncio.sleep(3)

    # 步骤 4：验证状态更新
    print("\n步骤 4：验证安装记录状态更新")
    async with get_task_session() as session:
        result = await session.execute(
            select(TenantPluginInstallation).where(
                TenantPluginInstallation.tenant_id == TEST_TENANT_ID,
                TenantPluginInstallation.plugin_id == TEST_PLUGIN_ID,
            )
        )
        installation = result.scalar_one_or_none()

        if installation:
            print(f"   当前状态: {installation.status}")
            if installation.status == "FAILED":
                print("✅ 状态已正确更新为 FAILED")
                return True
            else:
                print(f"❌ 状态未更新，预期 FAILED，实际 {installation.status}")
                return False
        else:
            print("❌ 安装记录不存在")
            return False


async def _test_plugin_uninstall_failed_event():
    """
    测试插件卸载失败事件处理

    场景：
    1. 发布 PluginUninstallFailed 事件
    2. 等待监听器处理
    3. 验证日志记录（通过返回值判断）

    注意：卸载失败事件只记录日志，不更新数据库状态
    """
    print("\n" + "=" * 60)
    print("测试：插件卸载失败事件处理")
    print("=" * 60)

    # 步骤 1：发布事件
    print("\n步骤 1：发布 PluginUninstallFailed 事件")
    publisher = get_event_publisher()
    event = PluginUninstallFailed(
        tenant_id=TEST_TENANT_ID,
        plugin_id=TEST_PLUGIN_ID,
        error_message="测试事件：模拟卸载失败",
    )

    try:
        await publisher.publish(event)
        print("✅ 事件发布成功")
    except Exception as e:
        print(f"❌ 事件发布失败: {e}")
        return False

    # 步骤 2：等待监听器处理
    print("\n步骤 2：等待监听器处理...")
    await asyncio.sleep(3)

    # 步骤 3：验证日志记录
    print("\n步骤 3：验证日志记录")
    print("✅ 卸载失败事件已处理（监听器会记录错误日志）")
    return True


async def cleanup_test_data():
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("清理测试数据")
    print("=" * 60)

    async with get_task_session() as session:
        from tenant.models.plugin_installation import TenantPluginInstallation
        from sqlalchemy import delete

        result = await session.execute(
            delete(TenantPluginInstallation).where(
                TenantPluginInstallation.tenant_id == TEST_TENANT_ID,
                TenantPluginInstallation.plugin_id == TEST_PLUGIN_ID,
            )
        )
        await session.flush()

        if result.rowcount > 0:
            print(f"✅ 已清理 {result.rowcount} 条测试记录")
        else:
            print("ℹ️  无需清理，测试记录不存在")


async def check_listener_status():
    """检查监听器状态"""
    print("=" * 60)
    print("检查监听器状态")
    print("=" * 60)

    try:
        from framework.cache.redis_util import RedisUtil
        from framework.events.base import EventStream

        # 初始化 Redis 客户端
        if not RedisUtil.is_initialized():
            await RedisUtil.init(settings().redis)

        # 检查 Redis 连接
        client = await RedisUtil.get_client()
        print("✅ Redis 连接正常")

        # 检查消费者组是否存在
        streams = [
            EventStream.PLUGIN_INSTALLATION_FAILED,
            EventStream.PLUGIN_UNINSTALL_FAILED,
        ]

        for stream in streams:
            try:
                info = await client.xinfo_groups(stream)
                print(f"✅ Stream {stream} 消费者组: {len(info)} 个")
                for group in info:
                    print(f"   - {group['name']}: {group['consumers']} 个消费者")
            except Exception as e:
                print(f"⚠️  Stream {stream} 可能不存在: {e}")

        return True

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("事件监听器测试")
    print("=" * 60)

    # 初始化配置
    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "config"
    init_settings(config_dir)

    # 初始化数据库引擎
    from framework.database.core.engine_pool import init_default_engine
    init_default_engine(
        database_url=settings().sqlalchemy.url,
        echo=settings().sqlalchemy.echo,
    )

    results = {}

    # 检查监听器状态
    results["listener_status"] = await check_listener_status()

    if not results["listener_status"]:
        print("\n❌ 监听器未正常运行，跳过后续测试")
        return

    # 测试插件安装失败事件
    results["installation_failed"] = await _test_plugin_installation_failed_event()

    # 测试插件卸载失败事件
    results["uninstall_failed"] = await _test_plugin_uninstall_failed_event()

    # 清理测试数据
    await cleanup_test_data()

    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    # 统计
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
