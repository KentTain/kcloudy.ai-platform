"""
Redis Stream 队列实现
"""

import json
import uuid
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from framework.core.queue import Message, QueueProvider
from framework.cache.redis_util import RedisUtil


class RedisQueue:
    """Redis Stream 队列实现"""

    def __init__(self, config: dict[str, Any]):
        self._config = config
        self._prefix = "queue:"

    def _get_stream_key(self, queue: str) -> str:
        """获取 Stream 键名"""
        return f"{self._prefix}{queue}"

    def _get_consumer_group(self, queue: str) -> str:
        """获取默认消费者组名"""
        return f"{queue}:group"

    async def enqueue(
        self,
        queue: str,
        message: dict[str, Any],
        delay: int | None = None
    ) -> str:
        """消息入队"""
        message_id = str(uuid.uuid4())
        body = json.dumps(message)

        stream_key = self._get_stream_key(queue)

        fields = {
            "id": message_id,
            "body": body,
            "timestamp": datetime.now().isoformat(),
        }

        result = await RedisUtil.xadd(stream_key, fields)
        return result

    async def dequeue(
        self,
        queue: str,
        count: int = 1,
        timeout: int = 0
    ) -> list[Message]:
        """消息出队"""
        stream_key = self._get_stream_key(queue)
        group = self._get_consumer_group(queue)

        # 确保消费者组存在
        try:
            await RedisUtil.xgroup_create(stream_key, group, id="0", mkstream=True)
        except Exception:
            pass  # 组已存在

        # 读取消息
        messages = await RedisUtil.xreadgroup(
            groupname=group,
            consumername=str(uuid.uuid4()),
            streams={stream_key: ">"},
            count=count,
            block=timeout * 1000 if timeout > 0 else None
        )

        result = []
        for stream_name, stream_messages in messages or []:
            for msg_id, fields in stream_messages:
                message = Message(
                    id=msg_id,
                    body=json.loads(fields.get("body", "{}")),
                    queue=queue,
                    timestamp=datetime.fromisoformat(fields.get("timestamp", datetime.now().isoformat())),
                    metadata={"group": group, "redis_id": msg_id}
                )
                result.append(message)

        return result

    async def ack(self, queue: str, message_id: str) -> bool:
        """确认消息"""
        stream_key = self._get_stream_key(queue)
        group = self._get_consumer_group(queue)

        try:
            await RedisUtil.xack(stream_key, group, message_id)
            return True
        except Exception:
            return False

    async def nack(self, queue: str, message_id: str) -> bool:
        """拒绝消息"""
        # Redis Stream 没有内置的 nack，消息会保留在 PEL 中
        return True

    async def get_queue_length(self, queue: str) -> int:
        """获取队列长度"""
        stream_key = self._get_stream_key(queue)
        info = await RedisUtil.xinfo_stream(stream_key)
        return info.get("length", 0) if info else 0

    async def purge(self, queue: str) -> bool:
        """清空队列"""
        stream_key = self._get_stream_key(queue)
        try:
            await RedisUtil.delete(stream_key)
            return True
        except Exception:
            return False

    async def create_consumer_group(
        self,
        queue: str,
        group: str,
        start_id: str = "0"
    ) -> bool:
        """创建消费者组"""
        stream_key = self._get_stream_key(queue)
        try:
            await RedisUtil.xgroup_create(stream_key, group, id=start_id, mkstream=True)
            return True
        except Exception:
            return False
