"""调度器生命周期单元测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSetupScheduler:
    """setup_scheduler 测试"""

    @pytest.mark.asyncio
    async def test_setup_registers_local_tasks(self):
        """WHEN: 调用 setup_scheduler()
        THEN: 本地任务注册到本地调度器"""
        mock_settings = MagicMock()

        with (
            patch("demo.tasks.setup.AsyncIOScheduler") as mock_sched_cls,
            patch("demo.tasks.setup.init_settings", return_value=mock_settings),
        ):
            mock_local = MagicMock()
            mock_cluster = MagicMock()
            mock_sched_cls.side_effect = [mock_local, mock_cluster]

            from demo.tasks.setup import setup_scheduler

            await setup_scheduler()

            mock_local.add_job.assert_called()
            mock_local.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_registers_cluster_tasks(self):
        """WHEN: 调用 setup_scheduler()
        THEN: 集群任务注册到集群调度器"""
        mock_settings = MagicMock()

        with (
            patch("demo.tasks.setup.AsyncIOScheduler") as mock_sched_cls,
            patch("demo.tasks.setup.init_settings", return_value=mock_settings),
            patch("demo.tasks.setup.RedisJobStore", return_value=MagicMock()),
        ):
            mock_local = MagicMock()
            mock_cluster = MagicMock()
            mock_sched_cls.side_effect = [mock_local, mock_cluster]

            from demo.tasks.setup import setup_scheduler

            await setup_scheduler()

            mock_cluster.add_job.assert_called()
            mock_cluster.start.assert_called_once()


class TestCleanupScheduler:
    """cleanup_scheduler 测试"""

    @pytest.mark.asyncio
    async def test_cleanup_shuts_down_schedulers(self):
        """WHEN: 调用 cleanup_scheduler()
        THEN: 所有运行中的调度器优雅停止"""
        mock_local = MagicMock()
        mock_local.running = True
        mock_cluster = MagicMock()
        mock_cluster.running = True

        with (
            patch("demo.tasks.setup._local_scheduler", mock_local, create=True),
            patch("demo.tasks.setup._cluster_scheduler", mock_cluster, create=True),
        ):
            from demo.tasks.setup import cleanup_scheduler

            await cleanup_scheduler()

            mock_local.shutdown.assert_called_once_with(wait=True)
            mock_cluster.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_cleanup_skips_not_running(self):
        """WHEN: 调度器未运行
        THEN: 不调用 shutdown"""
        mock_local = MagicMock()
        mock_local.running = False

        with patch("demo.tasks.setup._local_scheduler", mock_local, create=True):
            from demo.tasks.setup import cleanup_scheduler

            await cleanup_scheduler()

            mock_local.shutdown.assert_not_called()
