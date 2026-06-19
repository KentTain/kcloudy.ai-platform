"""Listeners 常量测试"""

import pytest


class TestPubSubConstants:
    """Pub/Sub 常量测试"""

    def test_heartbeat_topic_defined(self):
        """WHEN: 导入 HEARTBEAT_TOPIC
        THEN: 值为 'demo:heartbeat'"""
        from demo.listeners.services.pubsub.constants import (
            HEARTBEAT_TOPIC,
        )

        assert HEARTBEAT_TOPIC == "demo:heartbeat"


class TestQueueConstants:
    """Queue 常量测试"""

    def test_dataset_notify_queue_defined(self):
        """WHEN: 导入 DATASET_NOTIFY_QUEUE
        THEN: 值为 'demo:dataset:notify'"""
        from demo.listeners.services.queue.constants import (
            DATASET_NOTIFY_QUEUE,
        )

        assert DATASET_NOTIFY_QUEUE == "demo:dataset:notify"
