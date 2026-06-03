"""
Provider ID 解析类

迁移自 plugin/entities/plugin.py，用于解析和管理插件提供者的标识符。

Provider ID 格式：组织/插件名/提供者名
"""

import re


class ProviderIDFormatError(ValueError):
    """Provider ID 格式错误异常"""

    pass


class GenericProviderID:
    """
    通用提供者ID类

    解析和管理插件提供者的标识符，格式为：组织/插件名/提供者名
    """

    organization: str  # 组织名
    plugin_name: str  # 插件名
    provider_name: str  # 提供者名
    is_hardcoded: bool  # 是否为硬编码提供者

    def to_string(self) -> str:
        """转换为字符串格式"""
        return str(self)

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.organization}/{self.plugin_name}/{self.provider_name}"

    def __init__(self, value: str, is_hardcoded: bool = False) -> None:
        """
        初始化提供者ID

        :param value: 提供者ID字符串
        :param is_hardcoded: 是否为硬编码提供者
        :raises ProviderIDFormatError: 当提供者ID格式不正确时
        """
        if not value:
            raise ProviderIDFormatError("插件未找到，请添加插件")
        # 检查该值是否是具有指定格式的有效插件 ID: $organization/$plugin_name/$provider_name
        if not re.match(r"^[a-z0-9_-]+\/[a-z0-9_-]+\/[a-z0-9_-]+$", value):
            raise ProviderIDFormatError(f"无效的插件ID {value}")

        self.organization, self.plugin_name, self.provider_name = value.split("/")
        self.is_hardcoded = is_hardcoded

    def is_langgenius(self) -> bool:
        """
        检查是否为LangGenius组织

        :return: 是否为LangGenius组织
        """
        return self.organization == "langgenius"

    @property
    def plugin_id(self) -> str:
        """
        获取插件ID

        :return: 插件ID（组织/插件名）
        """
        return f"{self.organization}/{self.plugin_name}"


class ModelProviderID(GenericProviderID):
    """
    模型提供者ID类

    专门用于处理模型提供者的ID，包含特殊的兼容性处理

    支持两种格式：
    1. 完整格式：organization/plugin_name/provider_name
    2. 简化格式：plugin_id/provider_name（自动转换为 langgenius/plugin_id/provider_name）

    规格说明：
    - 简化格式如 `plugin-001/openai` 解析为：
      - plugin_id = "plugin-001" (不含 langgenius/ 前缀)
      - provider_type = "openai"
    """

    # 存储原始的 plugin_id（不含 langgenius/ 前缀）
    _original_plugin_id: str | None = None

    def __init__(self, value: str, is_hardcoded: bool = False) -> None:
        """
        初始化模型提供者ID

        包含对Google模型的特殊处理（映射到Gemini插件）

        :param value: 提供者ID字符串
        :param is_hardcoded: 是否为硬编码提供者
        :raises ProviderIDFormatError: 当提供者ID格式不正确时
        """
        # 处理简化格式：plugin_id/provider_name
        if "/" in value and value.count("/") == 1:
            # 简化格式，存储原始 plugin_id 并转换为完整格式
            plugin_id, provider_name = value.split("/")
            self._original_plugin_id = plugin_id
            value = f"langgenius/{plugin_id}/{provider_name}"

        super().__init__(value, is_hardcoded)

        # Google模型映射到Gemini插件
        if self.organization == "langgenius" and self.provider_name == "google":
            self.plugin_name = "gemini"

    @property
    def plugin_id(self) -> str:
        """
        获取插件ID

        对于简化格式（如 `plugin-001/openai`），返回原始的 plugin_id（不含 langgenius/ 前缀）
        对于完整格式，返回 organization/plugin_name

        :return: 插件ID
        """
        if self._original_plugin_id is not None:
            # 简化格式，返回原始 plugin_id
            return self._original_plugin_id
        # 完整格式，返回 organization/plugin_name
        return f"{self.organization}/{self.plugin_name}"


class ToolProviderID(GenericProviderID):
    """
    工具提供者ID类

    专门用于处理工具提供者的ID，包含特殊的兼容性处理

    支持两种格式：
    1. 完整格式：organization/plugin_name/provider_name
    2. 简化格式：plugin_id/provider_name（自动转换为 langgenius/plugin_id/provider_name）
    """

    def __init__(self, value: str, is_hardcoded: bool = False) -> None:
        """
        初始化工具提供者ID

        包含对特定工具提供者的插件名映射处理

        :param value: 提供者ID字符串
        :param is_hardcoded: 是否为硬编码提供者
        :raises ProviderIDFormatError: 当提供者ID格式不正确时
        """
        # 处理简化格式：plugin_id/provider_name
        if "/" in value and value.count("/") == 1:
            plugin_id, provider_name = value.split("/")
            value = f"langgenius/{plugin_id}/{provider_name}"

        super().__init__(value, is_hardcoded)

        # 特定工具提供者的插件名映射
        if self.organization == "langgenius":
            if self.provider_name in ["jina", "siliconflow", "stepfun", "gitee_ai"]:
                self.plugin_name = f"{self.provider_name}_tool"
