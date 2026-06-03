"""
插件数据库集成测试

验证 ai 插件相关表的 CRUD 操作。
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import text


pytestmark = pytest.mark.integration


class TestPluginTablesExist:
    """验证插件相关表是否存在"""

    @pytest_asyncio.fixture
    async def session(self, ai_async_engine):
        async with ai_async_engine.connect() as conn:
            yield conn

    @pytest.mark.asyncio
    async def test_plugins_table_exists(self, session):
        """验证 plugins 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugins')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_plugin_declarations_table_exists(self, session):
        """验证 plugin_declarations 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugin_declarations')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_plugin_installations_table_exists(self, session):
        """验证 plugin_installations 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugin_installations')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_plugin_credentials_table_exists(self, session):
        """验证 plugin_credentials 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugin_credentials')")
        )
        assert result.scalar() is True


class TestPluginCRUD:
    """插件 CRUD 集成测试"""

    @pytest_asyncio.fixture
    async def session(self, ai_async_engine):
        """使用事务隔离的测试会话"""
        async with ai_async_engine.connect() as conn:
            transaction = await conn.begin()
            yield conn
            await transaction.rollback()

    @pytest.mark.asyncio
    async def test_insert_plugin(self, session):
        """测试插入插件记录"""
        test_id = str(uuid.uuid4())
        result = await session.execute(
            text("""
                INSERT INTO ai.plugins (id, plugin_id, plugin_unique_identifier, refers, install_type, created_at, updated_at)
                VALUES (:id, 'test/plugin', :uid, 0, 'local', NOW(), NOW())
                RETURNING id
            """),
            {"id": test_id, "uid": f"test/plugin:1.0.0@{test_id[:8]}"}
        )
        assert result.scalar() == test_id


class TestForeignKeyConstraints:
    """外键约束测试"""

    @pytest_asyncio.fixture
    async def session(self, ai_async_engine):
        async with ai_async_engine.connect() as conn:
            yield conn

    @pytest.mark.asyncio
    async def test_plugin_installation_has_fk_constraints(self, session):
        """验证 plugin_installations 有外键约束"""
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND table_schema = 'ai' 
                AND table_name = 'plugin_installations'
            """)
        )
        # 至少有一个外键约束（tenant_id）
        assert result.scalar() >= 1

    @pytest.mark.asyncio
    async def test_plugin_credential_has_fk_constraints(self, session):
        """验证 plugin_credentials 有外键约束"""
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND table_schema = 'ai' 
                AND table_name = 'plugin_credentials'
            """)
        )
        # 至少有一个外键约束（tenant_id）
        assert result.scalar() >= 1
