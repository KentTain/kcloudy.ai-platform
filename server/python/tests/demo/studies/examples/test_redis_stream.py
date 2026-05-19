"""
Redis Stream 使用示例

演示 Redis Stream 的核心功能：
1. 基本操作：添加消息 (XADD)、读取消息 (XREAD)
2. 消费者组：创建消费者组 (XGROUP)、组内读取 (XREADGROUP)、确认消息 (XACK)
3. 高级功能：待处理消息查询 (XPENDING)、消费者信息 (XINFO)

运行方式：
    # 使用默认连接 (localhost:6379)
    python test_redis_stream.py

    # 指定 Redis 连接
    python test_redis_stream.py --host localhost --port 6379 --db 0

    # 使用密码
    python test_redis_stream.py --password your_password
"""

import asyncio
import argparse
import sys
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis
from loguru import logger


@dataclass
class RedisConfig:
    """Redis 连接配置"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None


class RedisStreamExample:
    """Redis Stream 示例类"""

    def __init__(self, config: RedisConfig):
        self.config = config
        self.redis: aioredis.Redis | None = None

    async def connect(self):
        """连接 Redis"""
        self.redis = aioredis.Redis(
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            password=self.config.password,
            decode_responses=True,  # 自动解码为字符串
        )
        await self.redis.ping()
        logger.info(f"已连接到 Redis: {self.config.host}:{self.config.port}")

    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.aclose()
            logger.info("Redis 连接已关闭")

    # ==================== 基本操作 ====================

    async def add_message(self, stream_name: str, data: dict[str, Any]) -> str:
        """
        向流中添加消息

        Args:
            stream_name: 流名称
            data: 消息数据字典

        Returns:
            消息ID
        """
        message_id = await self.redis.xadd(stream_name, data)
        logger.info(f"✅ 添加消息到流 '{stream_name}': ID={message_id}, data={data}")
        return message_id

    async def read_messages(
        self, stream_name: str, count: int = 1, block: int | None = None
    ) -> list:
        """
        从流中读取消息（非阻塞或阻塞）

        Args:
            stream_name: 流名称
            count: 读取的消息数量
            block: 阻塞时间（毫秒），None 表示非阻塞

        Returns:
            消息列表
        """
        if block:
            # 阻塞读取
            messages = await self.redis.xread(
                {stream_name: "$"}, count=count, block=block
            )
        else:
            # 非阻塞读取，从最新消息开始
            messages = await self.redis.xread({stream_name: "0"}, count=count)

        logger.info(
            f"📖 从流 '{stream_name}' 读取到 {len(messages) if messages else 0} 条消息"
        )
        return messages

    async def get_stream_length(self, stream_name: str) -> int:
        """获取流中的消息数量"""
        length = await self.redis.xlen(stream_name)
        logger.info(f"📊 流 '{stream_name}' 的长度: {length}")
        return length

    async def get_stream_range(
        self,
        stream_name: str,
        start: str = "-",
        end: str = "+",
        count: int | None = None,
    ) -> list:
        """
        获取流中指定范围的消息

        Args:
            stream_name: 流名称
            start: 起始ID，"-" 表示最小ID
            end: 结束ID，"+" 表示最大ID
            count: 返回的消息数量
        """
        messages = await self.redis.xrange(stream_name, start, end, count)
        logger.info(f"📖 从流 '{stream_name}' 获取范围消息: {len(messages)} 条")
        return messages

    # ==================== 消费者组操作 ====================

    async def create_consumer_group(
        self, stream_name: str, group_name: str, start_id: str = "0"
    ) -> bool:
        """
        创建消费者组

        Args:
            stream_name: 流名称
            group_name: 消费者组名称
            start_id: 开始消费的位置，"0" 表示从头开始，"$" 表示从最新消息开始

        Returns:
            是否创建成功
        """
        try:
            await self.redis.xgroup_create(
                stream_name, group_name, start_id, mkstream=True
            )
            logger.info(
                f"✅ 创建消费者组 '{group_name}' 在流 '{stream_name}' (start_id={start_id})"
            )
            return True
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"ℹ️  消费者组 '{group_name}' 已存在")
                return True
            logger.error(f"❌ 创建消费者组失败: {e}")
            return False

    async def read_with_consumer_group(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block: int | None = None,
    ) -> list:
        """
        使用消费者组读取消息

        Args:
            stream_name: 流名称
            group_name: 消费者组名称
            consumer_name: 消费者名称
            count: 读取的消息数量
            block: 阻塞时间（毫秒）

        Returns:
            消息列表
        """
        # ">" 表示只读取新消息（从未被任何消费者读取过的消息）
        messages = await self.redis.xreadgroup(
            group_name, consumer_name, {stream_name: ">"}, count=count, block=block
        )
        logger.info(
            f"📖 消费者 '{consumer_name}' 从组 '{group_name}' 读取到 {len(messages) if messages else 0} 条新消息"
        )
        return messages

    async def acknowledge_message(
        self, stream_name: str, group_name: str, message_id: str
    ) -> int:
        """
        确认消息已处理

        Args:
            stream_name: 流名称
            group_name: 消费者组名称
            message_id: 消息ID

        Returns:
            确认的消息数量（1 或 0）
        """
        result = await self.redis.xack(stream_name, group_name, message_id)
        if result:
            logger.info(f"✅ 消息 {message_id} 已确认")
        else:
            logger.warning(f"⚠️  消息 {message_id} 确认失败")
        return result

    async def get_pending_messages(
        self, stream_name: str, group_name: str, count: int = 10
    ) -> dict:
        """
        获取消费者组的待处理消息

        Args:
            stream_name: 流名称
            group_name: 消费者组名称
            count: 返回的消息数量

        Returns:
            待处理消息信息
        """
        pending = await self.redis.xpending(stream_name, group_name)
        logger.info(f"📋 待处理消息信息: {pending}")

        # 获取具体的待处理消息
        pending_messages = await self.redis.xpending_range(
            stream_name, group_name, "-", "+", count
        )
        logger.info(f"📋 待处理消息详情 (前 {count} 条): {len(pending_messages)} 条")
        return {"summary": pending, "messages": pending_messages}

    async def get_consumer_info(self, stream_name: str, group_name: str) -> list:
        """获取消费者组中的消费者信息"""
        consumers = await self.redis.xinfo_consumers(stream_name, group_name)
        logger.info(f"👥 消费者组 '{group_name}' 的消费者信息:")
        for consumer in consumers:
            logger.info(f"   - {consumer}")
        return consumers

    async def get_group_info(self, stream_name: str) -> list:
        """获取流的所有消费者组信息"""
        groups = await self.redis.xinfo_groups(stream_name)
        logger.info(f"👥 流 '{stream_name}' 的消费者组信息:")
        for group in groups:
            logger.info(f"   - {group}")
        return groups

    async def delete_consumer(
        self, stream_name: str, group_name: str, consumer_name: str
    ) -> int:
        """
        删除消费者

        Args:
            stream_name: 流名称
            group_name: 消费者组名称
            consumer_name: 消费者名称

        Returns:
            被删除的消费者 pending 消息数量
        """
        result = await self.redis.xgroup_delconsumer(
            stream_name, group_name, consumer_name
        )
        logger.info(
            f"🗑️  删除消费者 '{consumer_name}': {result} 条 pending 消息被重新分配"
        )
        return result


# ==================== 示例演示 ====================


async def example_basic_operations(example: RedisStreamExample):
    """示例1: 基本操作 - 添加和读取消息"""
    logger.info("\n" + "=" * 60)
    logger.info("示例1: 基本操作 - 添加和读取消息")
    logger.info("=" * 60)

    stream_name = "mystream"

    # 1. 添加消息
    await example.add_message(stream_name, {"name": "Alice", "age": "30"})
    await example.add_message(stream_name, {"name": "Bob", "age": "25"})
    await example.add_message(stream_name, {"name": "Charlie", "age": "35"})

    # 2. 获取流长度
    await example.get_stream_length(stream_name)

    # 3. 读取所有消息
    messages = await example.get_stream_range(stream_name)
    # xrange 返回格式: [(message_id, {field: value, ...}), ...]
    for msg_id, fields in messages:
        logger.info(f"   消息 ID={msg_id}, 内容={fields}")


async def example_consumer_group(example: RedisStreamExample):
    """示例2: 消费者组 - 多消费者协作"""
    logger.info("\n" + "=" * 60)
    logger.info("示例2: 消费者组 - 多消费者协作")
    logger.info("=" * 60)

    stream_name = "task_stream"
    group_name = "task_processors"

    # 1. 创建消费者组（从头开始消费）
    await example.create_consumer_group(stream_name, group_name, start_id="0")

    # 2. 添加任务消息
    logger.info("\n添加任务消息...")
    for i in range(5):
        await example.add_message(stream_name, {"task_id": str(i), "type": "process"})

    # 3. 消费者1读取消息
    logger.info("\n消费者1 读取任务...")
    messages1 = await example.read_with_consumer_group(
        stream_name, group_name, "consumer_1", count=2
    )
    for _, msg_list in messages1:
        for msg_id, fields in msg_list:
            logger.info(f"   消费者1 收到: ID={msg_id}, 内容={fields}")

    # 4. 消费者2读取消息
    logger.info("\n消费者2 读取任务...")
    messages2 = await example.read_with_consumer_group(
        stream_name, group_name, "consumer_2", count=2
    )
    for _, msg_list in messages2:
        for msg_id, fields in msg_list:
            logger.info(f"   消费者2 收到: ID={msg_id}, 内容={fields}")

    # 5. 查看待处理消息
    await example.get_pending_messages(stream_name, group_name)

    # 6. 查看消费者信息
    await example.get_consumer_info(stream_name, group_name)


async def example_message_acknowledgement(example: RedisStreamExample):
    """示例3: 消息确认机制"""
    logger.info("\n" + "=" * 60)
    logger.info("示例3: 消息确认机制")
    logger.info("=" * 60)

    stream_name = "order_stream"
    group_name = "order_processors"

    # 1. 创建消费者组
    await example.create_consumer_group(stream_name, group_name)

    # 2. 添加订单消息
    await example.add_message(stream_name, {"order_id": "ORD001", "amount": "100"})
    await example.add_message(stream_name, {"order_id": "ORD002", "amount": "200"})

    # 3. 读取消息
    messages = await example.read_with_consumer_group(
        stream_name, group_name, "order_consumer", count=2
    )

    # 4. 确认消息
    for _, msg_list in messages:
        for msg_id, fields in msg_list:
            logger.info(f"处理订单: {fields}")
            # 模拟处理完成后确认
            await example.acknowledge_message(stream_name, group_name, msg_id)

    # 5. 再次查看待处理消息（应该为空）
    await example.get_pending_messages(stream_name, group_name)


async def example_pending_recovery(example: RedisStreamExample):
    """示例4: 从待处理消息恢复（模拟崩溃场景）"""
    logger.info("\n" + "=" * 60)
    logger.info("示例4: 从待处理消息恢复（模拟崩溃场景）")
    logger.info("=" * 60)

    stream_name = "job_stream"
    group_name = "job_workers"

    # 1. 创建消费者组
    await example.create_consumer_group(stream_name, group_name)

    # 2. 添加任务
    await example.add_message(stream_name, {"job_id": "JOB001", "status": "pending"})
    await example.add_message(stream_name, {"job_id": "JOB002", "status": "pending"})

    # 3. 模拟消费者1读取消息但未确认就崩溃了
    logger.info("\n模拟消费者1 读取消息后崩溃...")
    messages = await example.read_with_consumer_group(
        stream_name, group_name, "worker_1", count=2
    )
    for _, msg_list in messages:
        for msg_id, fields in msg_list:
            logger.info(
                f"   消费者1 读取到: ID={msg_id}, 内容={fields}（未确认就崩溃了）"
            )

    # 4. 查看待处理消息
    logger.info("\n查看待处理消息...")
    await example.get_pending_messages(stream_name, group_name)

    # 5. 消费者2接管并处理待处理消息
    logger.info("\n消费者2 接管待处理消息...")
    # 使用 ID "0" 表示读取待处理消息
    pending_messages = await example.redis.xreadgroup(
        group_name, "worker_2", {stream_name: "0"}, count=10
    )

    for _, msg_list in pending_messages:
        for msg_id, fields in msg_list:
            logger.info(f"   消费者2 重新处理: ID={msg_id}, 内容={fields}")
            await example.acknowledge_message(stream_name, group_name, msg_id)
            logger.info(f"   ✅ 消息 {msg_id} 已确认")

    # 6. 再次查看待处理消息（应该为空）
    await example.get_pending_messages(stream_name, group_name)


async def example_blocking_read(example: RedisStreamExample):
    """示例5: 阻塞读取（实时消息处理）"""
    logger.info("\n" + "=" * 60)
    logger.info("示例5: 阻塞读取（实时消息处理）")
    logger.info("=" * 60)

    stream_name = "event_stream"
    group_name = "event_handlers"

    # 创建消费者组
    await example.create_consumer_group(stream_name, group_name)

    # 启动一个后台任务定期添加消息
    async def produce_events():
        for i in range(3):
            await asyncio.sleep(1)
            await example.add_message(
                stream_name,
                {
                    "event": f"event_{i}",
                    "timestamp": str(asyncio.get_event_loop().time()),
                },
            )

    # 启动生产者
    producer_task = asyncio.create_task(produce_events())

    # 消费者阻塞读取新消息（2秒超时）
    logger.info("\n消费者阻塞读取新消息（最多等待2秒）...")
    messages = await example.read_with_consumer_group(
        stream_name, group_name, "event_consumer", count=10, block=2000
    )

    for _, msg_list in messages:
        for msg_id, fields in msg_list:
            logger.info(f"   🎉 收到事件: {fields}")
            await example.acknowledge_message(stream_name, group_name, msg_id)

    # 等待生产者完成
    await producer_task


# ==================== 主函数 ====================


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Redis Stream 使用示例")
    parser.add_argument("--host", default="localhost", help="Redis 主机")
    parser.add_argument("--port", type=int, default=6379, help="Redis 端口")
    parser.add_argument("--db", type=int, default=0, help="Redis 数据库")
    parser.add_argument("--password", help="Redis 密码")
    args = parser.parse_args()

    # 创建配置
    config = RedisConfig(
        host=args.host, port=args.port, db=args.db, password=args.password
    )

    # 创建示例实例
    example = RedisStreamExample(config)

    try:
        # 连接 Redis
        await example.connect()

        # 运行所有示例
        await example_basic_operations(example)
        await example_consumer_group(example)
        await example_message_acknowledgement(example)
        await example_pending_recovery(example)
        await example_blocking_read(example)

        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有示例运行完成！")
        logger.info("=" * 60)

    finally:
        # 关闭连接
        await example.close()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    # 运行主函数
    asyncio.run(main())
