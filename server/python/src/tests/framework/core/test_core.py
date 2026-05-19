"""
core 模块单元测试

验证 Protocol 接口定义是否正确。
"""

import pytest
from typing import Protocol, runtime_checkable

from framework.core.storage import StorageProvider
from framework.core.queue import QueueProvider, Message
from framework.core.pubsub import PubSubProvider
from framework.core.lock import LockProvider, Lock


class TestStorageProtocol:
    """StorageProvider Protocol 测试"""

    def test_is_protocol(self):
        """
        场景：验证是 Protocol
        WHEN: 检查 StorageProvider
        THEN: 是 Protocol 子类
        """
        assert isinstance(StorageProvider, type)

    def test_implementation_satisfies_protocol(self):
        """
        场景：实现满足协议
        WHEN: 创建满足所有方法的类
        THEN: 被视为 StorageProvider
        """

        class MockStorage:
            async def upload(self, bucket: str, name: str, data: bytes, content_type: str | None = None) -> str:
                return f"{bucket}/{name}"

            async def download(self, bucket: str, name: str) -> bytes:
                return b"data"

            async def delete(self, bucket: str, name: str) -> bool:
                return True

            async def exists(self, bucket: str, name: str) -> bool:
                return True

            async def get_presigned_url(self, bucket: str, name: str, expires: int = 3600) -> str:
                return "https://example.com/file"

            async def list_objects(self, bucket: str, prefix: str = "", recursive: bool = True) -> list[str]:
                return []

            async def bucket_exists(self, bucket: str) -> bool:
                return True

            async def create_bucket(self, bucket: str) -> bool:
                return True

        # 使用 isinstance 检查（因为使用了 @runtime_checkable）
        storage = MockStorage()
        assert isinstance(storage, StorageProvider)


class TestQueueProtocol:
    """QueueProvider Protocol 测试"""

    def test_message_dataclass(self):
        """
        场景：Message 数据类
        WHEN: 创建 Message 实例
        THEN: 正确初始化
        """
        msg = Message(
            id="msg-123",
            body={"data": "test"},
            queue="test-queue"
        )

        assert msg.id == "msg-123"
        assert msg.body == {"data": "test"}
        assert msg.queue == "test-queue"
        assert msg.metadata == {}

    def test_implementation_satisfies_protocol(self):
        """
        场景：实现满足协议
        WHEN: 创建满足所有方法的类
        THEN: 被视为 QueueProvider
        """

        class MockQueue:
            async def enqueue(self, queue: str, message: dict, delay: int | None = None) -> str:
                return "msg-id"

            async def dequeue(self, queue: str, count: int = 1, timeout: int = 0) -> list[Message]:
                return []

            async def ack(self, queue: str, message_id: str) -> bool:
                return True

            async def nack(self, queue: str, message_id: str) -> bool:
                return True

            async def get_queue_length(self, queue: str) -> int:
                return 0

            async def purge(self, queue: str) -> bool:
                return True

            async def create_consumer_group(self, queue: str, group: str, start_id: str = "0") -> bool:
                return True

        queue = MockQueue()
        assert isinstance(queue, QueueProvider)


class TestPubSubProtocol:
    """PubSubProvider Protocol 测试"""

    def test_implementation_satisfies_protocol(self):
        """
        场景：实现满足协议
        WHEN: 创建满足所有方法的类
        THEN: 被视为 PubSubProvider
        """

        class MockPubSub:
            async def publish(self, topic: str, message: dict) -> bool:
                return True

            async def subscribe(self, topic: str, handler) -> bool:
                return True

            async def unsubscribe(self, topic: str) -> bool:
                return True

            async def get_subscribers(self, topic: str) -> int:
                return 0

            async def pattern_subscribe(self, pattern: str, handler) -> bool:
                return True

        pubsub = MockPubSub()
        assert isinstance(pubsub, PubSubProvider)


class TestLockProtocol:
    """LockProvider Protocol 测试"""

    def test_lock_dataclass(self):
        """
        场景：Lock 数据类
        WHEN: 创建 Lock 实例
        THEN: 正确初始化
        """
        lock = Lock(
            key="resource-key",
            value="lock-value",
            ttl=30
        )

        assert lock.key == "resource-key"
        assert lock.value == "lock-value"
        assert lock.ttl == 30

    def test_implementation_satisfies_protocol(self):
        """
        场景：实现满足协议
        WHEN: 创建满足所有方法的类
        THEN: 被视为 LockProvider
        """

        class MockLock:
            async def acquire(self, key: str, ttl: int, timeout: int | None = None, retry_interval: float = 0.1) -> Lock | None:
                return Lock(key=key, value="value", ttl=ttl)

            async def release(self, lock: Lock) -> bool:
                return True

            async def extend(self, lock: Lock, ttl: int) -> bool:
                return True

            async def is_locked(self, key: str) -> bool:
                return False

            async def force_release(self, key: str) -> bool:
                return True

        lock_provider = MockLock()
        assert isinstance(lock_provider, LockProvider)
