"""
流式内容打印器

提供统一的流式内容打印功能，支持大语言模型和工具调用的输入输出格式化显示
"""

import json
import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from ai_plugin.sdk.entities.model.llm import LLMResultChunk
from ai_plugin.sdk.entities.model.message import PromptMessage, PromptMessageTool
from ai_plugin.sdk.entities.tool import ToolInvokeMessage


class PrintSession:
    """
    打印会话类

    管理单个调用会话的所有输入输出信息
    """

    def __init__(self, session_id: str, session_type: str):
        self.session_id = session_id
        self.session_type = session_type  # "llm" or "tool"
        self.start_time = datetime.now()
        self.end_time: datetime | None = None
        self.metadata: dict[str, Any] = {}  # 存储模型名称、工具名称等
        self.input_content: list[str] = []  # 输入内容
        self.output_content: list[str] = []  # 输出内容
        self.completed = False

    def add_input(self, content: str):
        """添加输入内容"""
        self.input_content.append(content)

    def add_output(self, content: str):
        """添加输出内容"""
        self.output_content.append(content)

    def set_metadata(self, **kwargs):
        """设置元数据"""
        self.metadata.update(kwargs)

    def complete(self):
        """标记会话完成"""
        self.end_time = datetime.now()
        self.completed = True

    def get_duration(self) -> float:
        """获取调用耗时（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()


class StreamPrinter:
    """
    流式内容打印器类

    提供统一的打印接口，支持LLM和工具调用的流式内容显示
    """

    def __init__(self):
        """初始化流式打印器"""
        self.sessions: dict[str, PrintSession] = {}

    def create_session(self, session_type: str, **metadata) -> str:
        """
        创建新的打印会话

        Args:
            session_type: 会话类型 ("llm" 或 "tool")
            **metadata: 会话元数据

        Returns:
            str: 会话ID
        """
        session_id = str(uuid.uuid4())
        session = PrintSession(session_id, session_type)
        session.set_metadata(**metadata)
        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> PrintSession | None:
        """获取会话"""
        return self.sessions.get(session_id)

    def complete_session(self, session_id: str):
        """完成会话并打印结果"""
        session = self.sessions.get(session_id)
        if not session:
            return

        session.complete()
        # 暂时关闭打印
        # self._print_session_result(session)

        # 清理已完成的会话
        del self.sessions[session_id]

    def _print_session_result(self, session: PrintSession):
        """打印会话结果"""
        try:
            # 构建完整的输出内容
            output_lines = []

            # 会话头部信息
            output_lines.append(f"\n{'=' * 80}")
            output_lines.append(f"🆔 会话ID: {session.session_id}")
            output_lines.append(
                f" 开始时间: {session.start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
            )
            output_lines.append(
                f" 结束时间: {session.end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if session.end_time else '进行中'}",
            )
            output_lines.append(f" 耗时: {session.get_duration():.3f} 秒")

            # 会话类型特定信息
            if session.session_type == "llm":
                output_lines.extend(self._build_llm_session_info(session))
            elif session.session_type == "tool":
                output_lines.extend(self._build_tool_session_info(session))

            # 输入内容
            if session.input_content:
                output_lines.append("\n 输入内容:")
                output_lines.append("─" * 50)
                for content in session.input_content:
                    output_lines.append(content.rstrip("\n"))

            # 输出内容
            if session.output_content:
                output_lines.append("\n💬 输出结果:")
                output_lines.append("─" * 50)
                # 将输出内容合并成一个字符串，然后分行处理
                output_text = "".join(session.output_content)
                if output_text:
                    # 移除末尾的换行符，然后重新分行
                    output_text = output_text.rstrip("\n")
                    if output_text:
                        output_lines.append(output_text)

            output_lines.append(f"\n{'=' * 80}\n")

            # 一次性原子打印所有内容
            complete_output = "\n".join(output_lines)
            print(complete_output, flush=True)

        except Exception as e:
            logger.exception(f"打印会话结果失败: {e}")

    def _build_llm_session_info(self, session: PrintSession) -> list[str]:
        """构建LLM会话信息字符串列表"""
        metadata = session.metadata
        info_lines = []

        info_lines.append(" 类型: 大语言模型调用")
        if metadata.get("plugin_id"):
            info_lines.append(f" 插件ID: {metadata['plugin_id']}")
        if metadata.get("provider"):
            info_lines.append(f"🏭 提供商: {metadata['provider']}")
        if metadata.get("model"):
            info_lines.append(f"🔮 模型: {metadata['model']}")
        if metadata.get("user_id"):
            info_lines.append(f"👤 用户ID: {metadata['user_id']}")

        # 构建可用工具信息
        tools = metadata.get("tools")
        if tools:
            info_lines.append(f" 可用工具数量: {len(tools)}")
            for i, tool in enumerate(tools, 1):
                info_lines.append(f"   {i}. {tool.name} - {tool.description}")
                if hasattr(tool, "parameters") and tool.parameters:
                    # 简化显示参数结构
                    params = tool.parameters
                    if isinstance(params, dict) and "properties" in params:
                        param_names = list(params["properties"].keys())
                        if param_names:
                            info_lines.append(
                                f"       参数: {', '.join(param_names[:3])}{'...' if len(param_names) > 3 else ''}",
                            )

        return info_lines

    def _build_tool_session_info(self, session: PrintSession) -> list[str]:
        """构建工具会话信息字符串列表"""
        metadata = session.metadata
        info_lines = []

        info_lines.append(" 类型: 工具调用")
        if metadata.get("plugin_id"):
            info_lines.append(f" 插件ID: {metadata['plugin_id']}")
        if metadata.get("tool_provider"):
            info_lines.append(f"🏭 工具提供商: {metadata['tool_provider']}")
        if metadata.get("tool_name"):
            info_lines.append(f" 工具名称: {metadata['tool_name']}")
        if metadata.get("user_id"):
            info_lines.append(f"👤 用户ID: {metadata['user_id']}")

        return info_lines

    # ===== 通用格式化方法 =====

    def format_content(self, content: Any, max_length: int = 1000) -> str:
        """
        格式化任意内容，处理截取逻辑

        Args:
            content: 要格式化的内容
            max_length: 最大长度，超过此长度会被截取

        Returns:
            str: 格式化后的内容
        """
        if not content:
            return ""

        try:
            # 处理字符串类型内容
            if isinstance(content, str):
                text_content = content
            # 处理列表类型内容
            elif isinstance(content, list):
                text_parts = []
                for item in content:
                    if hasattr(item, "data"):
                        text_parts.append(str(item.data))
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                text_content = "".join(text_parts)
            # 处理字典类型内容
            elif isinstance(content, dict):
                text_content = json.dumps(content, ensure_ascii=False, indent=2)
            else:
                text_content = str(content)

            # 截取内容
            if len(text_content) > max_length:
                text_content = text_content[:max_length] + "..."

            return text_content.strip()

        except Exception as e:
            logger.exception(f"格式化内容失败: {e}")
            return str(content)[:max_length] if content else ""

    def print_section_header(self, title: str, emoji: str = ""):
        """
        打印章节标题

        Args:
            title: 标题内容
            emoji: 前缀表情符号
        """
        print(f"\n{emoji} {title}:")
        print("─" * 50)

    def print_separator(self, length: int = 50):
        """
        打印分隔线

        Args:
            length: 分隔线长度
        """
        print("─" * length)

    def hide_sensitive_data(
        self, data: dict, sensitive_keys: list[str] | None = None
    ) -> dict:
        """
        隐藏敏感数据

        Args:
            data: 原始数据字典
            sensitive_keys: 敏感字段列表

        Returns:
            dict: 隐藏敏感信息后的数据字典
        """
        if sensitive_keys is None:
            sensitive_keys = ["api_key", "secret", "password", "token", "credentials"]

        result = {}
        for key, value in data.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                result[key] = "[已隐藏]"
            elif isinstance(value, dict):
                result[key] = self.hide_sensitive_data(value, sensitive_keys)
            else:
                result[key] = value
        return result

    # ===== LLM相关打印方法 =====

    def get_role_display_name(self, role) -> str:
        """
        获取角色的显示名称

        Args:
            role: 消息角色

        Returns:
            str: 角色显示名称
        """
        try:
            from ai_plugin.sdk.entities.model.message import PromptMessageRole

            role_map = {
                PromptMessageRole.SYSTEM: "system",
                PromptMessageRole.USER: "user",
                PromptMessageRole.ASSISTANT: "assistant",
                PromptMessageRole.TOOL: "tool",
            }

            if hasattr(role, "value"):
                # 如果是枚举，直接使用value
                return role.value
            elif role in role_map:
                return role_map[role]
            else:
                return str(role).lower()

        except Exception as e:
            logger.exception(f"获取角色显示名称失败: {e}")
            return str(role).lower()

    def collect_prompt_messages(
        self,
        session_id: str,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        max_content_length: int = 1000,
    ):
        """
        收集输入的提示消息到会话中

        Args:
            session_id: 会话ID
            prompt_messages: 提示消息列表
            tools: 可用工具列表
            max_content_length: 单条消息内容的最大长度
        """
        session = self.get_session(session_id)
        if not session:
            return

        try:
            # 收集可用工具信息
            if tools:
                session.set_metadata(tools=tools)
                session.add_input(" 可用工具:\n")
                for tool in tools:
                    session.add_input(f"   {tool.name}: {tool.description}\n")
                    # 格式化工具参数
                    if tool.parameters:
                        params_content = self.format_content(
                            tool.parameters, max_length=500
                        )
                        session.add_input(f"     参数结构: {params_content}\n")
                session.add_input("\n")

            # 收集提示消息
            if prompt_messages:
                for i, message in enumerate(prompt_messages):
                    # 获取角色显示名称
                    role_name = self.get_role_display_name(message.role)

                    # 格式化内容
                    content = self.format_content(message.content, max_content_length)

                    # 收集消息
                    if content:
                        session.add_input(f"{role_name}: {content}\n")
                    else:
                        session.add_input(f"{role_name}: [空消息]\n")

                    # 如果有工具调用信息，也收集
                    if hasattr(message, "tool_calls"):
                        tool_calls = getattr(message, "tool_calls", [])
                        if tool_calls:
                            for tool_call in tool_calls:
                                session.add_input(
                                    f"   工具调用: {tool_call.function.name}\n"
                                )
                                args_content = self.format_content(
                                    tool_call.function.arguments, max_content_length
                                )
                                session.add_input(f"   参数: {args_content}\n")

                    # 如果有工具调用ID，收集
                    if hasattr(message, "tool_call_id"):
                        tool_call_id = getattr(message, "tool_call_id", "")
                        if tool_call_id:
                            session.add_input(f"   工具调用ID: {tool_call_id}\n")

        except Exception as e:
            logger.exception(f"收集提示消息失败: {e}")

    def collect_llm_stream_content(self, session_id: str, chunk: LLMResultChunk):
        """
        收集大语言模型流式返回的单个内容块

        Args:
            session_id: 会话ID
            chunk: LLM结果块
        """
        session = self.get_session(session_id)
        if not session:
            return

        try:
            delta = chunk.delta
            message = delta.message

            # 收集文本内容
            if message.content:
                # 如果内容是字符串类型，直接收集
                if isinstance(message.content, str):
                    session.add_output(message.content)
                # 如果内容是列表类型，处理每个内容块
                elif isinstance(message.content, list):
                    for content_item in message.content:
                        if hasattr(content_item, "data"):
                            session.add_output(content_item.data)

            # 收集工具调用信息
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    session.add_output(f"\n 工具调用: {tool_call.function.name}\n")
                    session.add_output(f" 参数: {tool_call.function.arguments}\n")
                    session.add_output("─" * 50 + "\n")

        except Exception as e:
            logger.exception(f"收集流式内容失败: {e}")

    # ===== 工具调用相关打印方法 =====

    def collect_tool_invoke_params(
        self,
        session_id: str,
        tool_provider: str,
        tool_name: str,
        tool_parameters: dict,
        credentials: dict | None = None,
        user_id: str | None = None,
    ):
        """
        收集工具调用的入参到会话中

        Args:
            session_id: 会话ID
            tool_provider: 工具提供者
            tool_name: 工具名称
            tool_parameters: 工具参数
            credentials: 凭证信息（可选）
            user_id: 用户ID（可选）
        """
        session = self.get_session(session_id)
        if not session:
            return

        try:
            session.add_input(f" 工具提供者: {tool_provider}\n")
            session.add_input(f" 工具名称: {tool_name}\n")

            if user_id:
                session.add_input(f"👤 用户ID: {user_id}\n")

            # 收集参数，格式化JSON
            if tool_parameters:
                session.add_input(" 工具参数:\n")
                formatted_params = self.format_content(tool_parameters, max_length=2000)
                session.add_input(f"   {formatted_params}\n")

            # 收集凭证（隐藏敏感信息）
            if credentials:
                safe_credentials = self.hide_sensitive_data(credentials)
                session.add_input("🔑 凭证信息:\n")
                formatted_creds = self.format_content(safe_credentials, max_length=500)
                session.add_input(f"   {formatted_creds}\n")

        except Exception as e:
            logger.exception(f"收集工具调用参数失败: {e}")

    def collect_tool_invoke_message(self, session_id: str, message: ToolInvokeMessage):
        """
        收集工具调用返回的单个消息到会话中

        Args:
            session_id: 会话ID
            message: 工具调用消息
        """
        session = self.get_session(session_id)
        if not session:
            return

        try:
            message_type = message.type
            message_content = message.message

            if message_content is None:
                return

            # 根据消息类型进行不同的处理
            if message_type == ToolInvokeMessage.MessageType.TEXT:
                if hasattr(message_content, "text"):
                    session.add_output(getattr(message_content, "text", ""))

            elif message_type == ToolInvokeMessage.MessageType.JSON:
                if hasattr(message_content, "json_object"):
                    json_obj = getattr(message_content, "json_object", {})
                    json_str = self.format_content(json_obj, max_length=2000)
                    session.add_output(f"\n JSON数据: {json_str}\n")

            elif message_type == ToolInvokeMessage.MessageType.BLOB:
                if hasattr(message_content, "blob"):
                    blob_data = getattr(message_content, "blob", b"")
                    blob_size = len(blob_data) if blob_data else 0
                    session.add_output(f"\n📁 二进制数据: {blob_size} 字节\n")

            elif message_type == ToolInvokeMessage.MessageType.LOG:
                if hasattr(message_content, "level") and hasattr(
                    message_content, "message"
                ):
                    level_emoji = {
                        "DEBUG": "🐛",
                        "INFO": "",
                        "WARNING": "",
                        "ERROR": "",
                        "CRITICAL": "",
                    }.get(
                        getattr(message_content, "level", ""),
                        "",
                    )
                    msg_text = getattr(message_content, "message", "")
                    level_text = getattr(message_content, "level", "")
                    session.add_output(f"\n{level_emoji} [{level_text}] {msg_text}\n")

            elif message_type == ToolInvokeMessage.MessageType.VARIABLE:
                if hasattr(message_content, "name") and hasattr(
                    message_content, "value"
                ):
                    name = getattr(message_content, "name", "")
                    value = getattr(message_content, "value", "")
                    session.add_output(f"\n🔢 变量 {name} = {value}\n")
            else:
                # 其他类型的消息，尝试直接收集
                content_str = self.format_content(message_content, max_length=1000)
                session.add_output(f"\n🔹 [{message_type.value}] {content_str}\n")

        except Exception as e:
            logger.exception(f"收集工具调用消息失败: {e}")
