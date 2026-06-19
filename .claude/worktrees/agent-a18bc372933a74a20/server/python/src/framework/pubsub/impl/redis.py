"""
Redis PubSub 实现
"""

import asyncio
import json
from typing import Any, Callable

from framework.core.pubsub import PubSubProvider
from framework.cache.redis_util import RedisUtil


class RedisPubSub:
    """Redis PubSub 实现"""

    def __init__(self, config: dict[str, Any]):
        self._config = config
        self._subscribers: dict[str, list[Callable]] = {}
        self._running = False

    async def publish(self, topic: str, message: dict[str, Any]) -> bool:
        """发布消息"""
        try:
            body = json.dumps(message)
            await RedisUtil.publish(topic, body)
            return True
        except Exception:
            return False

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[str, dict[str, Any]], None]
    ) -> bool:
        """订阅主题"""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

        return True

    async def unsubscribe(self, topic: str) -> bool:
        """取消订阅"""
        if topic in self._subscribers:
            del self._subscribers[topic]
        return True

    async def get_subscribers(self, topic: str) -> int:
        """获取订阅者数量"""
        try:
            result = await RedisUtil.pubsub_numsub(topic)
            return result.get(topic, 0)
        except Exception:
            return 0

    async def pattern_subscribe(
        self,
        pattern: str,
        handler: Callable[[str, dict[str, Any]], None]
    ) -> bool:
        """模式订阅"""
        # 简化实现，将模式作为普通主题处理
        return await self.subscribe(pattern, handler)

    async def start_listening(self) -> None:
        """开始监听消息"""
        self._running = True

        while self._running:
            try:
                # 获取所有订阅的主题
                topics = list(self._subscribers.keys())
                if not topics:
                    await asyncio.sleep(1)
                    continue

                # 监听消息
                message = await RedisUtil.get_message(timeout=1)
                if message:
                    topic = message.get("channel")
                    data = message.get("data")

                    if topic and isinstance(data, str):
                        try:
                            body = json.loads(data)
                        except json.JSONDecodeError:
                            body = {"raw": data}

                        # 调用处理器
                        handlers = self._subscribers.get(topic, [])
                        for handler in handlers:
                            try:
                                await handler(topic, body)
                            except Exception as e:
                                print(f"消息处理器错误: {e}")

            except Exception as e:
                print(f"监听错误: {e}")
                await asyncio.sleep(1)

    async def stop_listening(self) -> None:
        """停止监听"""
        self._running = False
