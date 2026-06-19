"""
凭证服务模块

提供插件凭证的加密、解密、脱敏和格式校验功能。
使用 framework/utils/crypto.py 的 AES-256-GCM 加密。
"""

import re
from typing import Any

from loguru import logger

from framework.utils.crypto import encrypt, decrypt

_logger = logger.bind(name=__name__)


class CredentialService:
    """凭证服务

    提供凭证相关的加密、解密、脱敏和格式校验功能。
    """

    # 敏感字段类型，这些类型的字段需要加密存储
    SENSITIVE_FIELD_TYPES = {"secret-input", "secret"}

    def encrypt_credentials(
        self,
        credentials: dict[str, Any],
        credentials_schema: list[dict],
    ) -> dict[str, Any]:
        """
        加密凭证中的敏感字段

        Args:
            credentials: 原始凭证字典
            credentials_schema: 凭证架构定义，用于识别敏感字段

        Returns:
            加密后的凭证字典
        """
        if not credentials:
            return {}

        encrypted_credentials = {}

        # 构建字段类型映射
        field_types = self._build_field_types_map(credentials_schema)

        for key, value in credentials.items():
            if value is None:
                encrypted_credentials[key] = None
                continue

            field_type = field_types.get(key)

            if field_type in self.SENSITIVE_FIELD_TYPES:
                # 敏感字段需要加密
                try:
                    encrypted_credentials[key] = encrypt(str(value))
                except Exception as e:
                    _logger.error(f"加密凭证字段 {key} 失败: {e}")
                    encrypted_credentials[key] = value
            else:
                # 非敏感字段直接存储
                encrypted_credentials[key] = value

        return encrypted_credentials

    def decrypt_credentials(
        self,
        encrypted_credentials: dict[str, Any],
        credentials_schema: list[dict],
    ) -> dict[str, Any]:
        """
        解密凭证中的敏感字段

        Args:
            encrypted_credentials: 加密的凭证字典
            credentials_schema: 凭证架构定义

        Returns:
            解密后的凭证字典
        """
        if not encrypted_credentials:
            return {}

        decrypted_credentials = {}

        # 构建字段类型映射
        field_types = self._build_field_types_map(credentials_schema)

        for key, value in encrypted_credentials.items():
            if value is None:
                decrypted_credentials[key] = None
                continue

            field_type = field_types.get(key)

            if field_type in self.SENSITIVE_FIELD_TYPES:
                # 敏感字段需要解密
                try:
                    decrypted_credentials[key] = decrypt(str(value))
                except Exception as e:
                    _logger.warning(f"解密凭证字段 {key} 失败: {e}")
                    decrypted_credentials[key] = value
            else:
                # 非敏感字段直接使用
                decrypted_credentials[key] = value

        return decrypted_credentials

    def mask_credentials(
        self,
        credentials: dict[str, Any],
        credentials_schema: list[dict],
    ) -> dict[str, Any]:
        """
        脱敏凭证中的敏感字段

        Args:
            credentials: 原始凭证字典
            credentials_schema: 凭证架构定义

        Returns:
            脱敏后的凭证字典
        """
        if not credentials:
            return {}

        masked_credentials = {}

        # 构建字段类型映射
        field_types = self._build_field_types_map(credentials_schema)

        for key, value in credentials.items():
            if value is None:
                masked_credentials[key] = None
                continue

            field_type = field_types.get(key)

            if field_type in self.SENSITIVE_FIELD_TYPES:
                # 敏感字段需要脱敏
                masked_credentials[key] = self._mask_sensitive_value(str(value))
            else:
                # 非敏感字段直接显示
                masked_credentials[key] = value

        return masked_credentials

    def validate_credentials_format(
        self,
        credentials: dict[str, Any],
        credentials_schema: list[dict],
    ) -> None:
        """
        验证凭证格式是否符合架构定义

        Args:
            credentials: 凭证字典
            credentials_schema: 凭证架构定义

        Raises:
            ValueError: 凭证格式不符合要求
        """
        if not credentials_schema:
            return

        for schema_item in credentials_schema:
            field_name = schema_item.get("name")
            if not field_name:
                continue

            field_value = credentials.get(field_name)
            field_type = schema_item.get("type", "string")
            required = schema_item.get("required", False)

            # 检查必填字段
            if required and field_value is None:
                raise ValueError(f"凭证字段 {field_name} 是必填的")

            # 跳过空值
            if field_value is None:
                continue

            # 检查数据类型
            if field_type in {"secret-input", "text-input", "string"}:
                if not isinstance(field_value, str):
                    raise ValueError(f"凭证字段 {field_name} 应该是字符串类型")

            elif field_type == "select":
                if not isinstance(field_value, str):
                    raise ValueError(f"凭证字段 {field_name} 应该是字符串类型")

                # 检查选项值
                options = schema_item.get("options", [])
                if options:
                    valid_options = []
                    for option in options:
                        if isinstance(option, dict):
                            valid_options.append(option.get("value"))
                        else:
                            valid_options.append(str(option))

                    if field_value not in valid_options:
                        raise ValueError(
                            f"凭证字段 {field_name} 的值应该是以下之一: {valid_options}"
                        )

            elif field_type == "number":
                if not isinstance(field_value, (int, float)):
                    raise ValueError(f"凭证字段 {field_name} 应该是数字类型")

            elif field_type == "boolean":
                if not isinstance(field_value, bool):
                    raise ValueError(f"凭证字段 {field_name} 应该是布尔类型")

    def extract_credentials_schema(
        self,
        plugin_config: dict[str, Any] | None,
    ) -> list[dict]:
        """
        从插件配置中提取凭证架构

        Args:
            plugin_config: 插件配置字典

        Returns:
            凭证架构列表
        """
        credentials_schema = []

        if not plugin_config:
            return credentials_schema

        tools_configuration = plugin_config.get("tools_configuration")
        if not tools_configuration:
            return credentials_schema

        for tool_provider_config in tools_configuration:
            schema = tool_provider_config.get("credentials_schema", [])
            if schema:
                credentials_schema.extend(schema)

        return credentials_schema

    def _build_field_types_map(
        self,
        credentials_schema: list[dict],
    ) -> dict[str, str]:
        """
        构建字段名称到类型的映射

        Args:
            credentials_schema: 凭证架构定义

        Returns:
            字段名称到类型的映射字典
        """
        field_types = {}

        if not credentials_schema:
            return field_types

        for schema_item in credentials_schema:
            if isinstance(schema_item, dict) and "name" in schema_item:
                field_types[schema_item["name"]] = schema_item.get("type", "string")

        return field_types

    def _mask_sensitive_value(self, value: str) -> str:
        """
        对敏感值进行脱敏处理

        Args:
            value: 原始值

        Returns:
            脱敏后的值
        """
        if not value:
            return value

        length = len(value)

        if length <= 8:
            # 短字符串只显示首尾各 2 个字符
            return f"{value[:2]}...{value[-2:]}" if length > 4 else "****"
        elif length <= 16:
            # 中等长度显示首尾各 4 个字符
            return f"{value[:4]}....{value[-4:]}"
        else:
            # 长字符串显示首尾各 5 个字符
            return f"{value[:5]}....{value[-5:]}"


# 全局服务实例
credential_service = CredentialService()
