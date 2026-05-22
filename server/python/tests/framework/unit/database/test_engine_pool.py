"""
DatabaseEnginePool 单元测试
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from framework.database.core.engine_pool import (
    DatabaseEnginePool,
    get_engine_pool,
    init_default_engine,
)
from framework.tenant.protocols import TenantDatabaseConfig
from framework.tenant.enums import DatabaseType


class TestDatabaseEnginePool:
    """DatabaseEnginePool 测试"""

    def test_pool_creation(self):
        """创建引擎池"""
        pool = DatabaseEnginePool(max_engines=10, idle_timeout=600)

        assert pool._max_engines == 10
        assert pool._idle_timeout == 600
        assert len(pool._engines) == 0

    def test_get_stats(self):
        """获取统计信息"""
        pool = DatabaseEnginePool()
        stats = pool.get_stats()

        assert "total_engines" in stats
        assert "max_engines" in stats
        assert "has_default" in stats

    def test_get_engine_pool_singleton(self):
        """全局单例"""
        pool1 = get_engine_pool()
        pool2 = get_engine_pool()

        assert pool1 is pool2


class TestDefaultEngine:
    """默认引擎测试"""

    def test_init_default_engine(self):
        """初始化默认引擎"""
        pool = DatabaseEnginePool()
        pool.init_default(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/test",
            echo=False,
        )

        assert pool._default_engine is not None
        assert pool._default_session_factory is not None

    def test_get_default_engine(self):
        """获取默认引擎"""
        pool = DatabaseEnginePool()
        pool.init_default("postgresql+asyncpg://user:pass@localhost:5432/test")

        engine = pool.get_engine(None, None)
        assert engine is pool._default_engine


class TestTenantEngine:
    """租户引擎测试"""

    def test_build_database_url_postgresql(self):
        """构建 PostgreSQL URL"""
        pool = DatabaseEnginePool()
        config = TenantDatabaseConfig(
            type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="tenant_db",
            username="user",
            password="pass",
        )

        url = pool._build_database_url(config)
        assert url.startswith("postgresql+asyncpg://")
        assert "tenant_db" in url

    def test_build_database_url_mysql(self):
        """构建 MySQL URL"""
        pool = DatabaseEnginePool()
        config = TenantDatabaseConfig(
            type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            database="tenant_db",
            username="user",
            password="pass",
        )

        url = pool._build_database_url(config)
        assert url.startswith("mysql+aiomysql://")
        assert "tenant_db" in url
