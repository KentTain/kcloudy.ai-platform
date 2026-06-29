"""
启动时插件目录扫描服务

在应用启动时自动扫描指定目录的插件包并注册到数据库。
"""

from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.services.plugin_definition_service import plugin_definition_service
from tenant.services.plugin_package_service import PluginPackageInfo, plugin_package_service

_logger = logger.bind(name=__name__)


@dataclass
class StartupScanResult:
    """启动扫描结果"""

    total_count: int = 0
    success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


async def scan_plugins_at_startup(
    session: AsyncSession,
    directory: str,
) -> StartupScanResult:
    """
    启动时扫描插件目录并注册

    扫描指定目录下的所有 .zip 插件包，解析并注册到数据库。
    扫描失败不抛出异常，仅记录错误并继续处理下一个文件。

    Args:
        session: 数据库会话
        directory: 要扫描的目录路径

    Returns:
        StartupScanResult: 扫描结果统计
    """
    result = StartupScanResult()
    scan_path = Path(directory)

    # 检查目录是否存在
    if not scan_path.exists():
        _logger.warning(f"插件目录不存在，跳过扫描: {directory}")
        return result

    if not scan_path.is_dir():
        _logger.warning(f"插件路径不是目录，跳过扫描: {directory}")
        return result

    # 递归收集所有 .zip 文件
    zip_files = list(scan_path.rglob("*.zip"))

    if not zip_files:
        _logger.info(f"插件目录为空，未找到 .zip 文件: {directory}")
        return result

    result.total_count = len(zip_files)
    _logger.info(f"开始扫描插件目录: {directory}，共 {result.total_count} 个 .zip 文件")

    for zip_file in zip_files:
        try:
            # 解析插件包
            package_info = plugin_package_service.parse_package_from_path(zip_file)
            package_data = zip_file.read_bytes()

            # 注册插件定义
            try:
                await plugin_definition_service.register_definition(
                    session=session,
                    package_info=package_info,
                    package_data=package_data,
                    overwrite=False,
                )
                result.success_count += 1
                _logger.info(
                    f"插件注册成功: {package_info.plugin_id}:{package_info.version}"
                )
            except Exception as e:
                error_msg = str(e)
                if "已存在" in error_msg:
                    result.skipped_count += 1
                    _logger.debug(
                        f"插件已存在，跳过: {package_info.plugin_id}:{package_info.version}"
                    )
                else:
                    result.failed_count += 1
                    result.errors.append(
                        f"{package_info.plugin_id}: {error_msg}"
                    )
                    _logger.warning(
                        f"插件注册失败: {package_info.plugin_id}, 错误: {error_msg}"
                    )

        except Exception as e:
            # 解析失败
            result.failed_count += 1
            result.errors.append(f"{zip_file.name}: 解析失败 - {str(e)}")
            _logger.warning(f"插件包解析失败: {zip_file}, 错误: {e}")

    _logger.info(
        f"插件目录扫描完成: 共 {result.total_count} 个, "
        f"成功 {result.success_count} 个, "
        f"跳过 {result.skipped_count} 个, "
        f"失败 {result.failed_count} 个"
    )

    return result
