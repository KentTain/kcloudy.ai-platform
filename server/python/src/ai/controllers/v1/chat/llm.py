"""LLM 对话控制器

提供流式对话接口和任务停止接口。
"""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
from typing import Any

import orjson
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from ai.listeners.services.pubsub.memory_task.constants import (
    ACTIVE_ASYNCIO_TASKS,
    TASK_TYPE_GENERATE_LLM,
)
from ai.listeners.services.pubsub.memory_task.helpers import stop_task_by_id
from ai.models.conversation import Conversation
from ai.models.enums import ConversationMode, ConversationStatus, MessageStatus
from ai.models.message import Message
from ai.schemas.chat import AIChatRequest, TextPart, UIMessage
from ai.schemas.completion import ErrorCode
from extended.langchain.agents.agent_factory import AgentFactory
from extended.langchain.models.alon_chat import AlonChatModel
from framework.common.ctx import get_tenant_id, get_user_id
from framework.database.core.engine import get_session

_logger = logger.bind(name=__name__)

# 默认应用配置
DEFAULT_APP_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_APP_NAME = "通用智能体"


class EventType(str, Enum):
    """SSE 事件类型（AI SDK UIMessageChunk 标准）"""

    START = "start"
    TEXT_START = "text-start"
    TEXT_DELTA = "text-delta"
    TEXT_END = "text-end"
    FINISH = "finish"
    ERROR = "error"


# 搜索类工具名称关键字
SEARCH_TOOL_KEYWORDS = frozenset(
    [
        "search",
        "baidu",
        "google",
        "bing",
        "duckduckgo",
        "websearch",
        "web_search",
    ]
)


def _is_search_tool(tool_name: str) -> bool:
    """判断是否为搜索类工具"""
    if not tool_name:
        return False
    tool_name_lower = tool_name.lower()
    return any(keyword in tool_name_lower for keyword in SEARCH_TOOL_KEYWORDS)


def _extract_user_query(messages: list[UIMessage]) -> str:
    """从消息列表提取用户查询

    从最后一条用户消息的 parts 中提取文本内容。

    Args:
        messages: UIMessage 消息列表

    Returns:
        用户查询文本

    Raises:
        ValueError: 如果无法提取有效查询
    """
    # 从后往前找最后一条用户消息
    for message in reversed(messages):
        if message.role == "user":
            # 从 parts 中提取文本
            for part in message.parts:
                if isinstance(part, TextPart):
                    return part.text
                # 处理 dict 类型的 part（Pydantic 可能解析为 dict）
                if isinstance(part, dict) and part.get("type") == "text":
                    return part.get("text", "")
    raise ValueError("无法从消息中提取用户查询")


def _format_sse_line(data: Any) -> str:
    """格式化 SSE 输出行"""
    try:
        if isinstance(data, str):
            return f"data: {data}\n\n"
        else:
            json_data = orjson.dumps(data).decode("utf-8")
            return f"data: {json_data}\n\n"
    except Exception:
        _logger.exception("格式化 SSE 数据时出错")
        return 'data: {"error": "Failed to format data"}\n\n'


router = APIRouter(prefix="/chat-messages", tags=["LLM对话"])


async def _sse_generator(
    event_queue: asyncio.Queue,
    message_id: str,
    max_timeout: int = 300,
) -> AsyncGenerator[str, None]:
    """SSE 事件生成器（AI SDK UIMessageChunk 格式）

    输出格式：
    - data: {"type":"start","messageId":"..."}
    - data: {"type":"text-start","id":"..."}
    - data: {"type":"text-delta","id":"...","delta":"..."}
    - data: {"type":"text-end","id":"..."}
    - data: {"type":"finish","finishReason":"stop","usage":{...}}
    - data: [DONE]
    """
    start_time = time.time()
    text_id = f"text-{uuid.uuid4().hex[:8]}"
    text_started = False

    # 发送 start 事件
    yield _format_sse_line({"type": EventType.START, "messageId": message_id})

    while True:
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=1.0)

            if event is None:
                _logger.debug("收到流结束信号")
                break

            event_type = event.get("type")

            # 处理文本增量事件
            if event_type == EventType.TEXT_DELTA:
                if not text_started:
                    yield _format_sse_line({"type": EventType.TEXT_START, "id": text_id})
                    text_started = True
                # 确保 text-delta 使用与 text-start/text-end 相同的 id
                event_with_correct_id = {**event, "id": text_id}
                yield _format_sse_line(event_with_correct_id)
            elif event_type == EventType.TEXT_END:
                if text_started:
                    yield _format_sse_line({"type": EventType.TEXT_END, "id": text_id})
                    text_started = False
            elif event_type == EventType.FINISH:
                # 确保文本块已关闭
                if text_started:
                    yield _format_sse_line({"type": EventType.TEXT_END, "id": text_id})
                yield _format_sse_line(event)
            elif event_type == EventType.ERROR:
                yield _format_sse_line(event)
            else:
                # 其他事件直接转发
                yield _format_sse_line(event)

            elapsed = time.time() - start_time
            if elapsed > max_timeout:
                _logger.warning(f"任务执行超时, 已运行 {elapsed:.2f} 秒")
                break

        except TimeoutError:
            continue
        except Exception as e:
            _logger.exception("处理事件流时出错")
            yield _format_sse_line(
                {
                    "type": EventType.ERROR,
                    "error": {"code": ErrorCode.MODEL_ERROR, "message": f"Event processing error: {str(e)}"},
                }
            )
            break

    # 发送 [DONE] 标记
    yield "data: [DONE]\n\n"


async def _update_message_status(
    message_id: str, status: MessageStatus, error_msg: str | None = None
) -> None:
    """更新消息状态"""
    try:
        async for session in get_session():
            message = await session.get(Message, message_id)
            if message:
                message.status = status
                if error_msg:
                    message.message_metadata = {"error": error_msg}
                await session.commit()
                _logger.info(f"消息状态已更新为 {status.value}: {message_id}")
    except Exception:
        _logger.exception(f"更新消息状态失败: {message_id}")


@router.post("")
async def chat_messages(
    chat_request: AIChatRequest = Body(..., description="聊天请求"),
) -> StreamingResponse:
    """LLM 对话接口（AI SDK 标准）

    支持流式对话和会话创建/恢复。
    使用 Vercel AI SDK 标准格式。
    """
    tenant_id = get_tenant_id()
    user_id = get_user_id()

    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="未授权访问")

    task_id = str(uuid.uuid4())
    # 如果 id 为 None，生成新的会话 ID
    conversation_id = chat_request.id or str(uuid.uuid4())
    message_id = chat_request.message_id  # 使用前端传来的消息 ID

    # 从消息列表提取用户查询
    try:
        query = _extract_user_query(chat_request.messages)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_queue = asyncio.Queue()

    try:
        # 创建或恢复会话
        is_new_conversation = False
        async for session in get_session():
            # 如果前端未传 id，说明是新会话，直接创建
            if chat_request.id is None:
                conversation = Conversation(
                    id=conversation_id,
                    tenant_id=tenant_id,
                    app_id=DEFAULT_APP_ID,
                    name="新对话",
                    status=ConversationStatus.NORMAL,
                    mode=ConversationMode.CHAT,
                    created_by=user_id,
                )
                session.add(conversation)
                await session.commit()
                is_new_conversation = True
            else:
                # 检查会话是否已存在
                existing_conversation = await Conversation.one_by_conditions(
                    session,
                    conditions=[
                        Conversation.id == conversation_id,
                        Conversation.tenant_id == tenant_id,
                    ],
                )
                if existing_conversation:
                    # 恢复已有会话
                    conversation = existing_conversation
                else:
                    # 创建新会话
                    conversation = Conversation(
                        id=conversation_id,
                        tenant_id=tenant_id,
                        app_id=DEFAULT_APP_ID,
                        name="新对话",
                        status=ConversationStatus.NORMAL,
                        mode=ConversationMode.CHAT,
                        created_by=user_id,
                    )
                    session.add(conversation)
                    await session.commit()
                    is_new_conversation = True

        # 创建初始消息记录（状态为 pending）
        async for session in get_session():
            user_message = Message(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                app_id=DEFAULT_APP_ID,
                conversation_id=conversation_id,
                role="user",
                content=query,
                status=MessageStatus.PENDING,
                created_by=user_id,
            )
            assistant_message = Message(
                id=message_id,
                tenant_id=tenant_id,
                app_id=DEFAULT_APP_ID,
                conversation_id=conversation_id,
                role="assistant",
                status=MessageStatus.PENDING,
                created_by=user_id,
            )
            session.add(user_message)
            session.add(assistant_message)
            await session.commit()

        # 创建 AlonChatModel
        model_config = chat_request.body.model
        model = AlonChatModel(
            model=model_config.name,
            provider=model_config.provider,
            tenant_id=tenant_id,
            user_id=user_id,
            model_parameters=model_config.completion_params,
        )

        # 创建 Agent
        agent_factory = AgentFactory(model)
        agent = agent_factory.create_executor()

        # LLM 运行任务
        async def run_llm_task():
            try:
                start_time = time.time()
                full_content = ""
                prompt_tokens = 0
                completion_tokens = 0

                # 流式运行 Agent
                async for event in agent.astream_events(
                    {"input": query},
                    version="v2",
                ):
                    event_name = event.get("event")

                    if event_name == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and chunk.content:
                            content = chunk.content
                            full_content += content
                            # 发送 text-delta 事件（AI SDK 格式）
                            await event_queue.put(
                                {
                                    "type": EventType.TEXT_DELTA,
                                    "id": f"text-{message_id}",
                                    "delta": content,
                                }
                            )

                    elif event_name == "on_chain_end":
                        usage = event.get("data", {}).get("output", {}).get("usage", {})
                        if usage:
                            prompt_tokens = usage.get("input_tokens", 0)
                            completion_tokens = usage.get("output_tokens", 0)

                end_time = time.time()
                latency = end_time - start_time

                # 发送 finish 事件（AI SDK 格式）
                await event_queue.put(
                    {
                        "type": EventType.FINISH,
                        "finishReason": "stop",
                        "usage": {
                            "promptTokens": prompt_tokens,
                            "completionTokens": completion_tokens,
                        },
                        "latency": latency,
                    }
                )

                # 更新会话名称（新会话）
                if is_new_conversation:
                    async for session in get_session():
                        new_name = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        await Conversation.update_by_id(
                            session,
                            conversation_id,
                            {
                                "name": new_name[:50]
                                if len(full_content) > 50
                                else f"对话：{full_content[:30]}"
                            },
                        )
                        await session.commit()

                # 更新消息状态为正常并保存内容
                async for session in get_session():
                    message = await session.get(Message, message_id)
                    if message:
                        message.content = full_content
                        message.status = MessageStatus.NORMAL
                        message.token_count = prompt_tokens + completion_tokens
                        await session.commit()

                await event_queue.put(None)

            except asyncio.CancelledError:
                _logger.info(f"对话任务 {task_id} 被取消")
                # 更新消息状态为已停止
                await _update_message_status(message_id, MessageStatus.STOPPED)
                await event_queue.put(None)
                raise
            except Exception as e:
                _logger.exception("对话任务出错")
                # 更新消息状态为错误
                await _update_message_status(message_id, MessageStatus.ERROR, str(e))
                await event_queue.put(
                    {
                        "type": EventType.ERROR,
                        "error": {
                            "code": ErrorCode.MODEL_ERROR,
                            "message": str(e),
                        },
                    }
                )
                await event_queue.put(None)
                raise
            finally:
                # 清理任务资源
                ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM].pop(task_id, None)

        # 创建任务并注册到活跃任务列表
        task = asyncio.create_task(run_llm_task())
        ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM][task_id] = task

        # 保留扩展 headers（非标准但有用）
        headers = {
            "X-Conversation-ID": conversation_id,
            "X-Message-ID": message_id,
        }

        return StreamingResponse(
            _sse_generator(
                event_queue=event_queue,
                message_id=message_id,
            ),
            media_type="text/event-stream",
            headers=headers,
        )

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("LLM 聊天出错")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/stop")
async def stop_chat_messages(conversation_id: str) -> dict:
    """停止对话

    发送停止信号取消正在进行的对话任务。
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=401, detail="未授权访问")

    # 验证会话存在
    conversation = None
    async for session in get_session():
        conversation = await Conversation.one_by_conditions(
            session,
            conditions=[Conversation.id == conversation_id],
        )

    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 检查租户归属
    if conversation.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 查找活跃任务
    task_id = None
    message_id = None
    for tid, task in ACTIVE_ASYNCIO_TASKS[TASK_TYPE_GENERATE_LLM].items():
        if not task.done():
            # 检查任务是否属于该会话（通过任务上下文判断）
            # 这里简化处理，实际可能需要维护任务与会话的映射关系
            task_id = tid
            break

    if task_id:
        result = await stop_task_by_id(
            task_id=task_id,
            task_type=TASK_TYPE_GENERATE_LLM,
            task_name="LLM对话任务",
            message_id=message_id,
        )
        return {"success": True, "message": result["message"]}

    return {"success": True, "message": "未找到活跃任务"}
