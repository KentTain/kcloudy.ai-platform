"""
插件安装任务消费者

从 Redis Stream 队列消费安装任务并执行安装逻辑。
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from ai.listeners.services.queue.install_task_executor import InstallTaskExecutor
from framework.cache.redis_util import RedisUtil
from framework.database.dependencies import get_task_session
from framework.tenant.context import TenantContext

if TYPE_CHECKING:
    from framework.configs.settings import Settings

_logger = logging.getLogger(__name__)

# 队列名称
INSTALL_TASK_QUEUE = "plugin_install_tasks"

# 消费者组名称
CONSUMER_GROUP = "ai_install_task_handlers_group"
CONSUMER_NAME = "ai_install_task_handler"

# 运行状态
_running = False
_listen_task: asyncio.Task | None = None


async def setup_install_task_consumer(settings: "Settings") -> None:
    """
    注册安装任务消费者

    创建消费者组并启动监听任务。

    Args:
        settings: 应用配置
    """
    global _running, _listen_task

    # 创建消费者组
    try:
        await RedisUtil.xgroup_create(
            INSTALL_TASK_QUEUE,
            CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        _logger.info(f"创建消费者组: {INSTALL_TASK_QUEUE} -> {CONSUMER_GROUP}")
    except Exception as e:
        # 消费者组可能已存在
        _logger.debug(f"消费者组已存在或创建失败: {INSTALL_TASK_QUEUE} -> {e}")

    # 启动监听任务
    _running = True
    _listen_task = asyncio.create_task(_consume_tasks())

    _logger.info("安装任务消费者注册完成")


async def cleanup_install_task_consumer() -> None:
    """取消安装任务消费者"""
    global _running, _listen_task

    _running = False

    if _listen_task:
        _listen_task.cancel()
        try:
            await _listen_task
        except asyncio.CancelledError:
            pass
        _listen_task = None

    _logger.info("安装任务消费者清理完成")


async def _consume_tasks() -> None:
    """
    消费安装任务循环

    从 Redis Stream 读取任务并执行安装逻辑。
    """
    global _running

    # 构建 streams 字典
    streams = {INSTALL_TASK_QUEUE: ">"}

    while _running:
        try:
            # 从 Redis Stream 读取消息
            messages = await RedisUtil.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams=streams,
                count=1,
                block=1000,  # 阻塞 1 秒
            )

            if not messages:
                continue

            # 处理每条消息
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    try:
                        # 解析任务数据
                        task_data = _parse_message_data(message_data)
                        if not task_data:
                            _logger.warning(f"无效的任务消息: {message_data}")
                            await RedisUtil.xack(stream_name, CONSUMER_GROUP, message_id)
                            continue

                        # 设置租户上下文
                        tenant_id = task_data.get("tenant_id")
                        if tenant_id:
                            TenantContext.set_tenant_id(tenant_id)

                        # 执行安装任务
                        executor = InstallTaskExecutor()
                        await executor.execute(task_data)

                        # 确认消息
                        await RedisUtil.xack(stream_name, CONSUMER_GROUP, message_id)

                    except Exception as e:
                        _logger.exception(
                            f"处理安装任务失败: message_id={message_id}, error={e}"
                        )
                        # 消息处理失败，不确认，等待重试

        except asyncio.CancelledError:
            _logger.info("安装任务消费任务被取消")
            break
        except Exception as e:
            _logger.exception(f"安装任务消费错误: {e}")
            await asyncio.sleep(1)


def _parse_message_data(message_data: dict) -> dict[str, Any] | None:
    """
    解析消息数据

    Args:
        message_data: Redis Stream 消息数据

    Returns:
        dict | None: 解析后的任务数据
    """
    if not message_data:
        return None

    import json

    # 消息格式: {"task_type": "plugin_install", "task_id": "...", "tenant_id": "...", ...}
    # 或旧格式: {"payload": "{...}"}
    payload = message_data.get("payload")
    if payload:
        try:
            if isinstance(payload, str):
                return json.loads(payload)
            return payload
        except json.JSONDecodeError:
            return None

    # 新格式：字段直接在消息中
    if message_data.get("task_id") and message_data.get("plugin_id"):
        result = dict(message_data)
        # auto_start 可能是字符串 "True"/"False"
        auto_start = result.get("auto_start")
        if isinstance(auto_start, str):
            result["auto_start"] = auto_start.lower() == "true"
        return result

    return None
