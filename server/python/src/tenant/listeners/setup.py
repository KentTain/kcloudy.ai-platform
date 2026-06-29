"""
Tenant 模块监听器生命周期管理

注册和管理 Tenant 模块的事件监听器。
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from framework.cache.redis_util import RedisUtil
from framework.events.base import EventStream
from tenant.listeners.handlers.plugin_handler import (
    PluginInstallationFailedHandler,
    PluginUninstallFailedHandler,
)

if TYPE_CHECKING:
    from framework.configs.settings import Settings

_logger = logging.getLogger(__name__)

# 消费者组名称
CONSUMER_GROUP = "tenant_plugin_handlers_group"
CONSUMER_NAME = "tenant_plugin_handler"

# 处理器实例
_handlers: list = []
_running = False
_listen_task: asyncio.Task | None = None


# Stream 和处理器映射
STREAM_HANDLERS = [
    (EventStream.PLUGIN_INSTALLATION_FAILED, PluginInstallationFailedHandler()),
    (EventStream.PLUGIN_UNINSTALL_FAILED, PluginUninstallFailedHandler()),
]


async def setup_listeners(settings: "Settings") -> None:
    """
    注册所有事件监听器

    创建消费者组并启动监听任务。

    Args:
        settings: 应用配置
    """
    global _handlers, _running, _listen_task

    _handlers = [handler for _, handler in STREAM_HANDLERS]

    # 检查 Redis 是否初始化
    if not RedisUtil.is_initialized():
        _logger.error("Redis 未初始化，无法启动事件监听器")
        return

    # 创建消费者组
    for stream_name, _ in STREAM_HANDLERS:
        success = await RedisUtil.xgroup_create(
            stream_name,
            CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        if success:
            _logger.info(f"创建消费者组成功: {stream_name} -> {CONSUMER_GROUP}")
        else:
            # 消费者组可能已存在，检查是否真的存在
            try:
                client = await RedisUtil.get_client()
                groups = await client.xinfo_groups(stream_name)
                group_names = [g["name"] for g in groups]
                if CONSUMER_GROUP in group_names:
                    _logger.info(f"消费者组已存在: {stream_name} -> {CONSUMER_GROUP}")
                else:
                    _logger.error(f"创建消费者组失败: {stream_name} -> {CONSUMER_GROUP}")
            except Exception as e:
                _logger.error(f"检查消费者组状态失败: {stream_name} -> {e}")

    # 启动监听任务
    _running = True
    _listen_task = asyncio.create_task(_listen_events())

    _logger.info("Tenant 事件监听器注册完成")


async def cleanup_listeners() -> None:
    """取消所有事件监听器"""
    global _running, _listen_task

    _running = False

    if _listen_task:
        _listen_task.cancel()
        try:
            await _listen_task
        except asyncio.CancelledError:
            pass
        _listen_task = None

    _logger.info("Tenant 事件监听器清理完成")


async def _listen_events() -> None:
    """
    监听事件循环

    从 Redis Stream 读取事件并分发给对应的处理器。
    """
    global _running

    # 构建 streams 字典: {stream_name: last_id}
    streams = {stream_name: ">" for stream_name, _ in STREAM_HANDLERS}

    # 构建 stream -> handler 映射
    handler_map = {stream_name: handler for stream_name, handler in STREAM_HANDLERS}

    while _running:
        try:
            # 从 Redis Stream 读取消息
            messages = await RedisUtil.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams=streams,
                count=10,
                block=1000,  # 阻塞 1 秒
            )

            if not messages:
                continue

            # 处理每条消息
            for stream_name, stream_messages in messages:
                handler = handler_map.get(stream_name)
                if not handler:
                    continue

                for message_id, message_data in stream_messages:
                    try:
                        # 调用处理器
                        await handler.handle(message_data)

                        # 确认消息
                        await RedisUtil.xack(stream_name, CONSUMER_GROUP, message_id)

                    except Exception as e:
                        _logger.exception(
                            f"处理事件失败: stream={stream_name}, "
                            f"message_id={message_id}, error={e}"
                        )
                        # 消息处理失败，不确认，等待重试

        except asyncio.CancelledError:
            _logger.info("事件监听任务被取消")
            break
        except Exception as e:
            _logger.exception(f"事件监听错误: {e}")
            await asyncio.sleep(1)
