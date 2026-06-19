"""
雪花ID 类型

提供雪花ID 类型字段定义。
"""

import time
from typing import Any

from sqlalchemy import BigInteger, TypeDecorator


class SnowflakeIDGenerator:
    """雪花ID 生成器"""

    def __init__(self, worker_id: int = 1, datacenter_id: int = 1):
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.last_timestamp = -1

        # 起始时间戳 (2024-01-01)
        self.epoch = 1704067200000

    def generate(self) -> int:
        """生成雪花ID"""
        timestamp = int(time.time() * 1000)

        if timestamp < self.last_timestamp:
            raise ValueError("时钟回拨")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 4095
            if self.sequence == 0:
                timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        return (
            ((timestamp - self.epoch) << 22)
            | (self.datacenter_id << 17)
            | (self.worker_id << 12)
            | self.sequence
        )

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """等待下一毫秒"""
        timestamp = int(time.time() * 1000)
        while timestamp <= last_timestamp:
            timestamp = int(time.time() * 1000)
        return timestamp


# 全局生成器
_id_generator = SnowflakeIDGenerator()


class BigIntegerSnowflakeID(TypeDecorator):
    """
    雪花ID 类型

    数据库存储为 BigInteger，Python 中自动生成。
    """

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> int | None:
        """绑定参数时处理"""
        if value is None:
            return _id_generator.generate()

        return int(value)
