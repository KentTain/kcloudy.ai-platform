"""
Tasks 调度器集成测试

测试双调度器与真实 Redis 的交互。
"""

import asyncio

import pytest

pytestmark = pytest.mark.integration


class TestSchedulerIntegration:
    """调度器集成测试"""

    @pytest.mark.asyncio
    async def test_local_scheduler_runs_heartbeat(
        self, integration_settings
    ):
        """WHEN: 启动本地调度器
        THEN: heartbeat_task 在间隔内被触发"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from demo.tasks.services.heartbeat_task import heartbeat_task

        # 使用默认的 MemoryJobStore
        scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

        executed = []

        async def tracked_heartbeat():
            await heartbeat_task()
            executed.append(True)

        scheduler.add_job(
            tracked_heartbeat,
            "interval",
            seconds=1,
            id="test_heartbeat",
            max_instances=1,
        )
        scheduler.start()

        await asyncio.sleep(2)

        scheduler.shutdown(wait=False)

        assert len(executed) >= 1

    @pytest.mark.asyncio
    async def test_cluster_scheduler_with_redis(
        self, integration_settings, redis_available
    ):
        """WHEN: 启动集群调度器
        THEN: 集群任务注册到 Redis JobStore"""
        if not redis_available:
            pytest.skip("Redis 不可用")

        from apscheduler.jobstores.redis import RedisJobStore
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        redis_config = (
            integration_settings.messaging.connections.get(
                "redis", {}
            )
        )
        host = redis_config.get(
            "host", integration_settings.redis.single.host
        )
        port = redis_config.get(
            "port", integration_settings.redis.single.port
        )
        password = redis_config.get(
            "password", integration_settings.redis.single.password or ""
        )
        db = redis_config.get("db", 0)

        # RedisJobStore 使用单独的参数，不支持 url
        jobstore = RedisJobStore(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
        )

        scheduler = AsyncIOScheduler(
            jobstores={"default": jobstore},
            timezone="Asia/Shanghai",
        )

        # 使用可序列化的函数引用（模块:函数名格式）
        scheduler.add_job(
            "demo.tasks.services.heartbeat_task:heartbeat_task",
            "interval",
            minutes=5,
            id="test_cluster_task",
            replace_existing=True,
        )
        scheduler.start()

        jobs = scheduler.get_jobs()
        assert len(jobs) >= 1
        assert any(j.id == "test_cluster_task" for j in jobs)

        scheduler.shutdown(wait=False)
