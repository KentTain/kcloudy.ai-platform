from collections.abc import Generator
from typing import Any

from ai_plugin.sdk.entities.tool import ToolInvokeMessage, ToolProviderType
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class ToolInvocation(BackwardsInvocation[ToolInvokeMessage]):
    """
    工具调用类

    提供各种类型工具调用的统一接口
    """

    def invoke_builtin_tool(
        self,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用内置工具

        Args:
            provider: 提供者名称
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            Generator[ToolInvokeMessage, None, None]: 工具调用消息生成器
        """
        return self.invoke(ToolProviderType.BUILT_IN, provider, tool_name, parameters)

    def invoke_workflow_tool(
        self,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用工作流工具

        Args:
            provider: 提供者名称
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            Generator[ToolInvokeMessage, None, None]: 工具调用消息生成器
        """
        return self.invoke(ToolProviderType.WORKFLOW, provider, tool_name, parameters)

    def invoke_api_tool(
        self,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用API工具

        Args:
            provider: 提供者名称
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            Generator[ToolInvokeMessage, None, None]: 工具调用消息生成器
        """
        return self.invoke(ToolProviderType.API, provider, tool_name, parameters)

    def invoke(
        self,
        provider_type: ToolProviderType,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        通用工具调用方法

        Args:
            provider_type: 提供者类型
            provider: 提供者名称
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            Generator[ToolInvokeMessage, None, None]: 工具调用消息生成器
        """
        return self._backwards_invoke(
            InvokeType.Tool,
            ToolInvokeMessage,
            {
                "tool_type": provider_type.value,
                "provider": provider,
                "tool": tool_name,
                "tool_parameters": parameters,
            },
        )
