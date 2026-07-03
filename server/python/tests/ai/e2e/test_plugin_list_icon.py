"""
插件列表图标验证测试

测试插件列表 API 返回的数据中是否包含图标信息。

运行方式：
    uv run pytest -m e2e tests/ai/e2e/test_plugin_list_icon.py -v
"""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.services.plugin import plugin_management_service
from framework.tenant.context import TenantContext
from tests.ai.e2e.helpers.plugin_test_helper import PluginTestHelper


class TestPluginListIcon:
    """插件列表图标验证测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_available_plugins_list_contains_icon(
        self,
        e2e_session: AsyncSession,
        test_tenant_id: str,
        plugin_package_path: callable,
        cleanup_test_resources: dict,
        plugin_provider,
    ) -> None:
        """
        测试可用插件列表包含图标信息

        场景：获取可用插件列表
        - 安装 tongyi 插件
        - 获取可用插件列表
        - 验证列表中的插件包含图标字段
        - 验证图标 URL 格式正确
        - 验证已安装插件的图标信息完整
        """
        # 初始化
        TenantContext.set_tenant_id(test_tenant_id)
        helper = PluginTestHelper(test_tenant_id)

        # 获取插件包路径
        tongyi_path: Path = plugin_package_path("tongyi")
        plugin_id = "langgenius/tongyi"

        # -------------------------------------------------------------------------
        # 步骤 1：安装插件
        # -------------------------------------------------------------------------
        installed_plugin_id = await helper.install_plugin_from_path(
            e2e_session,
            str(tongyi_path),
        )
        assert installed_plugin_id == plugin_id, (
            f"安装的插件 ID 应为 {plugin_id}，实际为 {installed_plugin_id}"
        )

        # 等待安装完成
        from ai.components.plugin.engine.models.enums import PluginStatus

        await helper.wait_for_plugin_status(
            e2e_session,
            plugin_id,
            PluginStatus.INACTIVE,
            timeout=60.0,
        )

        # -------------------------------------------------------------------------
        # 步骤 2：获取可用插件列表
        # -------------------------------------------------------------------------
        result = await plugin_management_service.get_available_plugins(
            session=e2e_session,
            keyword=None,
            type=None,
            is_recommended=None,
            page=1,
            page_size=20,
        )

        assert result is not None, "插件列表不应为空"
        assert result.total > 0, "应至少有一个可用插件"

        # -------------------------------------------------------------------------
        # 步骤 3：验证已安装插件在列表中
        # -------------------------------------------------------------------------
        installed_plugin_in_list = None
        for item in result.items:
            if item.plugin_id == plugin_id:
                installed_plugin_in_list = item
                break

        assert installed_plugin_in_list is not None, (
            f"已安装的插件 {plugin_id} 应在可用插件列表中"
        )

        # -------------------------------------------------------------------------
        # 步骤 4：验证插件图标字段存在
        # -------------------------------------------------------------------------
        assert hasattr(installed_plugin_in_list, "icon"), (
            "插件信息应包含 icon 字段"
        )

        icon = installed_plugin_in_list.icon
        assert icon is not None, f"插件 {plugin_id} 的图标不应为空"

        # -------------------------------------------------------------------------
        # 步骤 5：验证图标 URL 格式正确
        # -------------------------------------------------------------------------
        # 图标应该是相对路径（如 icon_s_en.png）或 API URL
        assert isinstance(icon, str), f"图标应为字符串类型，实际类型: {type(icon)}"

        # 验证图标路径不为空字符串
        assert icon.strip(), "图标路径不应为空字符串"

        # 如果是 URL 格式，验证路径正确
        if icon.startswith("/"):
            assert "/ai/console/v1/plugins/assets/" in icon, (
                f"图标 URL 应包含插件资源路径，实际: {icon}"
            )
            assert plugin_id in icon, f"图标 URL 应包含插件 ID，实际: {icon}"

        # 打印图标信息用于调试
        print(f"\n插件 {plugin_id} 图标信息:")
        print(f"  icon: {icon}")

        # -------------------------------------------------------------------------
        # 步骤 6：验证其他必要字段也存在
        # -------------------------------------------------------------------------
        assert installed_plugin_in_list.name, "插件名称不应为空"
        assert installed_plugin_in_list.author, "插件作者不应为空"
        assert installed_plugin_in_list.version, "插件版本不应为空"
        assert installed_plugin_in_list.plugin_type, "插件类型不应为空"

        print(f"\n插件完整信息:")
        print(f"  plugin_id: {installed_plugin_in_list.plugin_id}")
        print(f"  name: {installed_plugin_in_list.name}")
        print(f"  author: {installed_plugin_in_list.author}")
        print(f"  version: {installed_plugin_in_list.version}")
        print(f"  icon: {installed_plugin_in_list.icon}")
        print(f"  plugin_type: {installed_plugin_in_list.plugin_type}")
        print(f"  is_installed: {installed_plugin_in_list.is_installed}")

        # -------------------------------------------------------------------------
        # 清理资源
        # -------------------------------------------------------------------------
        if "plugins" not in cleanup_test_resources:
            cleanup_test_resources["plugins"] = []
        cleanup_test_resources["plugins"].append(plugin_id)
