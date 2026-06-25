"""
插件包解析服务

提供插件包的解析、校验和计算、格式验证功能。
"""

import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


@dataclass
class PluginPackageInfo:
    """插件包解析结果"""

    plugin_id: str  # 插件ID，格式：author/name
    version: str  # 版本号
    author: str  # 作者
    name: str  # 插件名称
    package_hash: str  # 插件包 SHA256 校验和
    declaration: dict[str, Any]  # 完整声明内容
    manifest_type: str | None = None  # 清单类型


class PluginPackageService:
    """插件包解析服务"""

    # 支持的清单文件名
    MANIFEST_FILES = ["manifest.yaml", "manifest.yml"]

    @staticmethod
    def parse_package_from_bytes(package_data: bytes) -> PluginPackageInfo:
        """
        从字节数据解析插件包

        Args:
            package_data: 插件包二进制数据

        Returns:
            PluginPackageInfo: 解析结果

        Raises:
            ValueError: 插件包格式无效
        """
        # 计算校验和
        package_hash = hashlib.sha256(package_data).hexdigest()

        # 创建临时目录解压
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 保存插件包
            package_file = temp_path / "plugin.zip"
            package_file.write_bytes(package_data)

            # 验证并解压
            return PluginPackageService._parse_extracted_package(
                package_file, package_hash
            )

    @staticmethod
    def parse_package_from_path(package_path: Path) -> PluginPackageInfo:
        """
        从文件路径解析插件包

        Args:
            package_path: 插件包文件路径

        Returns:
            PluginPackageInfo: 解析结果

        Raises:
            ValueError: 插件包格式无效
            FileNotFoundError: 文件不存在
        """
        if not package_path.exists():
            raise FileNotFoundError(f"插件包不存在: {package_path}")

        if not package_path.is_file():
            raise ValueError(f"路径不是文件: {package_path}")

        if package_path.suffix.lower() != ".zip":
            raise ValueError(f"插件包必须是 .zip 格式: {package_path}")

        # 计算校验和
        package_data = package_path.read_bytes()
        package_hash = hashlib.sha256(package_data).hexdigest()

        return PluginPackageService._parse_extracted_package(package_path, package_hash)

    @staticmethod
    def _parse_extracted_package(
        package_path: Path, package_hash: str
    ) -> PluginPackageInfo:
        """
        解析已解压的插件包

        Args:
            package_path: 插件包文件路径
            package_hash: 插件包校验和

        Returns:
            PluginPackageInfo: 解析结果

        Raises:
            ValueError: 插件包格式无效
        """
        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                # 验证 ZIP 文件
                bad_file = zf.testzip()
                if bad_file:
                    raise ValueError(f"ZIP 文件损坏: {bad_file}")

                # 查找 manifest 文件
                manifest_path = None
                for manifest_file in PluginPackageService.MANIFEST_FILES:
                    manifest_candidates = [
                        name for name in zf.namelist() if name.endswith(manifest_file)
                    ]
                    if manifest_candidates:
                        manifest_path = manifest_candidates[0]
                        break

                if not manifest_path:
                    raise ValueError(
                        f"插件包中未找到 manifest 文件，支持的文件名: {PluginPackageService.MANIFEST_FILES}"
                    )

                # 读取 manifest 内容
                manifest_content = zf.read(manifest_path).decode("utf-8")
                manifest_data = yaml.safe_load(manifest_content)

                if not manifest_data:
                    raise ValueError("manifest 文件内容为空")

                # 验证必要字段
                required_fields = ["author", "name", "version"]
                missing_fields = [
                    field for field in required_fields if field not in manifest_data
                ]
                if missing_fields:
                    raise ValueError(
                        f"manifest 缺少必要字段: {', '.join(missing_fields)}"
                    )

                author = manifest_data.get("author", "")
                name = manifest_data.get("name", "")
                version = manifest_data.get("version", "")
                plugin_id = f"{author}/{name}"

                # 构建完整声明内容
                declaration = PluginPackageService._build_declaration(
                    manifest_data, zf
                )

                # 获取清单类型
                manifest_type = manifest_data.get("type")

                return PluginPackageInfo(
                    plugin_id=plugin_id,
                    version=version,
                    author=author,
                    name=name,
                    package_hash=package_hash,
                    declaration=declaration,
                    manifest_type=manifest_type,
                )

        except zipfile.BadZipFile:
            raise ValueError("无效的 ZIP 文件格式")
        except yaml.YAMLError as e:
            raise ValueError(f"manifest YAML 解析失败: {e}")

    @staticmethod
    def _build_declaration(
        manifest_data: dict[str, Any], zf: zipfile.ZipFile
    ) -> dict[str, Any]:
        """
        构建完整声明内容

        从 manifest 中提取配置信息，包括：
        - configuration: 基础配置
        - tools_configuration: 工具配置
        - models_configuration: 模型配置
        - agent_strategies_configuration: 代理策略配置

        Args:
            manifest_data: manifest 解析数据
            zf: ZIP 文件对象

        Returns:
            dict: 完整声明内容
        """
        declaration: dict[str, Any] = {
            "configuration": {},
            "tools_configuration": [],
            "models_configuration": [],
            "agent_strategies_configuration": [],
        }

        # 基础配置
        if "configuration" in manifest_data:
            declaration["configuration"] = manifest_data["configuration"]

        # 工具配置
        if "tools" in manifest_data:
            declaration["tools_configuration"] = manifest_data["tools"]

        # 模型配置
        if "models" in manifest_data:
            declaration["models_configuration"] = manifest_data["models"]

        # 代理策略配置
        if "agent_strategies" in manifest_data:
            declaration["agent_strategies_configuration"] = manifest_data[
                "agent_strategies"
            ]

        # 保留原始 manifest 数据
        declaration["_manifest"] = {
            "author": manifest_data.get("author"),
            "name": manifest_data.get("name"),
            "version": manifest_data.get("version"),
            "description": manifest_data.get("description"),
            "icon": manifest_data.get("icon"),
            "type": manifest_data.get("type"),
            "tags": manifest_data.get("tags", []),
        }

        return declaration

    @staticmethod
    def calculate_checksum(package_data: bytes) -> str:
        """
        计算插件包校验和

        Args:
            package_data: 插件包二进制数据

        Returns:
            str: SHA256 校验和
        """
        return hashlib.sha256(package_data).hexdigest()


# 单例实例
plugin_package_service = PluginPackageService()
