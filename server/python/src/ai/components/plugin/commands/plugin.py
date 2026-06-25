"""
插件系统管理命令
支持新重构的租户隔离、智能启动、冻结管理等功能
"""

import asyncio
import time

import click

from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory
from framework.database.dependencies import get_task_session
from framework.tenant.context import TenantContext


@click.group()
def plugin():
    """插件系统管理命令"""
    pass


@plugin.command()
@click.option("--tenant-id", default="system", help="租户ID")
@click.option("--package-path", type=click.Path(exists=True), help="插件包路径")
@click.option("--auto-start/--no-auto-start", default=False, help="是否自动启动")
def install(tenant_id: str, package_path: str | None, auto_start: bool):
    """安装插件"""

    async def _install():
        if not package_path:
            click.echo("请指定插件包路径")
            return

        try:
            TenantContext.set_tenant_id(tenant_id)
            async with get_task_session() as session:
                manager = await PluginManagerFactory.get_manager(tenant_id, session)

                click.echo(f" 开始安装插件: {package_path}")
                click.echo(f"   租户: {tenant_id}")
                click.echo(f"   自动启动: {auto_start}")

                # 读取插件包
                with open(package_path, "rb") as f:
                    package_data = f.read()

                # 创建安装请求
                from ai.components.plugin.engine.models.request import InstallRequest

                install_request = InstallRequest(auto_start=auto_start)

                # 安装插件
                plugin_id = await manager.install_plugin(package_data, install_request)

                click.echo(f" 插件安装成功: {plugin_id}")

        except Exception as e:
            click.echo(f"插件安装失败: {e}")

    asyncio.run(_install())


@plugin.command()
@click.option("--tenant-id", default="system", help="租户ID")
@click.option("--plugin-id", required=True, help="插件ID")
def start(tenant_id: str, plugin_id: str):
    """启动插件"""

    async def _start():
        try:
            TenantContext.set_tenant_id(tenant_id)
            async with get_task_session() as session:
                manager = await PluginManagerFactory.get_manager(tenant_id, session)

                click.echo(f" 启动插件: {plugin_id}")
                click.echo(f"   租户: {tenant_id}")

                success = await manager.start_plugin(plugin_id)

                if success:
                    click.echo(f" 插件启动成功: {plugin_id}")
                else:
                    click.echo(f"插件启动失败: {plugin_id}")

        except Exception as e:
            click.echo(f"插件启动失败: {e}")

    asyncio.run(_start())


@plugin.command()
@click.option("--tenant-id", default="system", help="租户ID")
@click.option("--plugin-id", help="插件ID")
def stop(tenant_id: str, plugin_id: str | None):
    """停止插件"""

    async def _stop():
        current_plugin_id = plugin_id  # 保存到局部变量
        try:
            TenantContext.set_tenant_id(tenant_id)
            async with get_task_session() as session:
                manager = await PluginManagerFactory.get_manager(tenant_id, session)

                if current_plugin_id:
                    # 停止单个插件
                    click.echo(f" 停止插件: {current_plugin_id}")
                    success = await manager.stop_plugin(current_plugin_id, session)
                    if success:
                        click.echo(f" 插件停止成功: {current_plugin_id}")
                    else:
                        click.echo(f"插件停止失败: {current_plugin_id}")
                else:
                    # 停止所有插件
                    click.echo(f" 停止租户所有插件: {tenant_id}")
                    stopped_count = 0
                    for pid in list(manager.running_plugins.keys()):
                        if await manager.stop_plugin(pid, session):
                            stopped_count += 1
                    click.echo(f" 停止完成: {stopped_count} 个插件")

        except Exception as e:
            if current_plugin_id:
                click.echo(f"插件停止失败: {current_plugin_id} - {e}")
            else:
                click.echo(f"插件停止失败: {e}")

    asyncio.run(_stop())


@plugin.command()
@click.option("--tenant-id", default="system", help="租户ID")
@click.option("--plugin-id", help="插件ID")
def health(tenant_id: str, plugin_id: str | None):
    """检查插件健康状态"""

    async def _health():
        try:
            TenantContext.set_tenant_id(tenant_id)
            async with get_task_session() as session:
                manager = await PluginManagerFactory.get_manager(tenant_id, session)

                if plugin_id:
                    # 检查单个插件
                    if plugin_id in manager.plugins:
                        plugin_info = manager.plugins[plugin_id]
                        click.echo(f"插件健康检查: {plugin_id}")
                        click.echo(f"   状态: {plugin_info.status}")
                        click.echo(f"   配置: {plugin_info.config}")
                        # 这里可以添加更多健康检查信息
                    else:
                        click.echo(f"插件不存在: {plugin_id}")
                else:
                    # 检查租户所有插件的健康状态
                    click.echo(f"租户 {tenant_id} 插件健康概览:")

                    status_counts = {}
                    for plugin_info in manager.plugins.values():
                        status = plugin_info.status
                        status_counts[status] = status_counts.get(status, 0) + 1

                    for status, count in status_counts.items():
                        click.echo(f"   {status}: {count} 个")

        except Exception as e:
            click.echo(f"健康检查失败: {e}")

    asyncio.run(_health())


@plugin.command()
@click.option("--tenant-id", default="system", help="租户ID")
@click.option("--plugin-id", required=True, help="插件ID")
@click.option("--action", required=True, help="调用的动作/方法名")
@click.option("--params", default="{}", help="JSON格式的参数")
@click.option("--timeout", default=30, type=int, help="超时时间（秒）")
def invoke(tenant_id: str, plugin_id: str, action: str, params: str, timeout: int):
    """调用插件方法"""

    async def _invoke():
        try:
            TenantContext.set_tenant_id(tenant_id)
            async with get_task_session() as session:
                manager = await PluginManagerFactory.get_manager(tenant_id, session)

                # 检查插件是否存在且正在运行
                if plugin_id not in manager.running_plugins:
                    click.echo(f"插件未运行: {plugin_id}")
                    click.echo("   请先启动插件再调用")
                    return

                click.echo(f" 调用插件方法: {plugin_id}.{action}")
                click.echo(f"   参数: {params}")
                click.echo(f"   超时: {timeout}秒")

                # 解析参数
                try:
                    import json

                    parameters = json.loads(params)
                except json.JSONDecodeError:
                    click.echo(f"参数解析失败，必须是有效的JSON格式: {params}")
                    return

                # 调用插件方法
                start_time = time.time()
                result = manager.invoke_plugin_stream(plugin_id, parameters, timeout)

                async for chunk in result:
                    # 格式化输出结果
                    if isinstance(result, dict):
                        import json

                        formatted_result = json.dumps(result, indent=2, ensure_ascii=False)
                        click.echo(formatted_result)
                    else:
                        click.echo(str(result))

                execution_time = (time.time() - start_time) * 1000  # 转换为毫秒

                click.echo(f" 调用成功 (耗时: {execution_time:.2f}ms)")
                click.echo("📤 返回结果:")

        except Exception as e:
            click.echo(f"调用失败: {e}")

    asyncio.run(_invoke())


if __name__ == "__main__":
    plugin()
