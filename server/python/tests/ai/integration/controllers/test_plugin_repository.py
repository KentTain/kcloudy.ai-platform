"""
插件数据库集成测试

验证 tenant 和 ai 插件相关表的 CRUD 操作。

架构变更（2026-06-25）：
- tenant.plugin_definitions：全局插件注册表（替代 ai.plugins + ai.plugin_declarations）
- tenant.plugin_installations：租户级安装记录
- ai.plugin_configs：插件配置
- ai.plugin_runtime_states：运行时状态
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

pytestmark = pytest.mark.integration


class TestNewPluginTablesExist:
    """验证新插件相关表是否存在"""

    @pytest_asyncio.fixture
    async def session(self, ai_async_engine):
        from sqlalchemy.ext.asyncio import AsyncSession
        session = AsyncSession(bind=ai_async_engine)
        try:
            yield session
        finally:
            try:
                await session.close()
            except RuntimeError:
                pass

    @pytest.mark.asyncio
    async def test_tenant_plugin_definitions_table_exists(self, session):
        """验证 tenant.plugin_definitions 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'tenant' AND table_name = 'plugin_definitions')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_tenant_plugin_installations_table_exists(self, session):
        """验证 tenant.plugin_installations 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'tenant' AND table_name = 'plugin_installations')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_ai_plugin_configs_table_exists(self, session):
        """验证 ai.plugin_configs 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugin_configs')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_ai_plugin_runtime_states_table_exists(self, session):
        """验证 ai.plugin_runtime_states 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugin_runtime_states')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_ai_plugin_credentials_table_exists(self, session):
        """验证 ai.plugin_credentials 表存在"""
        result = await session.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'plugin_credentials')")
        )
        assert result.scalar() is True


class TestPluginInstallationCRUD:
    """插件安装记录 CRUD 集成测试"""

    @pytest_asyncio.fixture
    async def session(self, ai_async_engine):
        """使用事务隔离的测试会话"""
        from sqlalchemy.ext.asyncio import AsyncSession
        session = AsyncSession(bind=ai_async_engine)
        try:
            yield session
        finally:
            try:
                await session.close()
            except RuntimeError:
                pass

    @pytest.mark.asyncio
    async def test_insert_plugin_definition(self, session):
        """测试插入插件定义记录"""
        test_id = str(uuid.uuid4())
        result = await session.execute(
            text("""
                INSERT INTO tenant.plugin_definitions
                (id, plugin_id, plugin_unique_identifier, refers, install_type, created_at, updated_at)
                VALUES (:id, 'test/plugin', :uid, 1, 'local', NOW(), NOW())
                RETURNING id
            """),
            {"id": test_id, "uid": f"test/plugin@1.0.0"}
        )
        assert result.scalar() == test_id

    @pytest.mark.asyncio
    async def test_insert_plugin_installation(self, session):
        """测试插入插件安装记录"""
        test_id = str(uuid.uuid4())
        tenant_id = "00000000-0000-0000-0000-000000000000"
        result = await session.execute(
            text("""
                INSERT INTO tenant.plugin_installations
                (id, tenant_id, plugin_id, plugin_unique_identifier, status, created_at, updated_at)
                VALUES (:id, :tenant_id, 'test/plugin', :uid, 'PENDING', NOW(), NOW())
                RETURNING id
            """),
            {"id": test_id, "tenant_id": tenant_id, "uid": f"test/plugin@1.0.0"}
        )
        assert result.scalar() == test_id


class TestForeignKeyConstraints:
    """外键约束测试"""

    @pytest_asyncio.fixture
    async def session(self, ai_async_engine):
        from sqlalchemy.ext.asyncio import AsyncSession
        session = AsyncSession(bind=ai_async_engine)
        try:
            yield session
        finally:
            try:
                await session.close()
            except RuntimeError:
                pass

    @pytest.mark.asyncio
    async def test_plugin_configs_has_unique_constraint(self, session):
        """验证 plugin_configs 有唯一约束"""
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                AND table_schema = 'ai'
                AND table_name = 'plugin_configs'
            """)
        )
        # tenant_id + plugin_id 唯一约束
        assert result.scalar() >= 1

    @pytest.mark.asyncio
    async def test_plugin_runtime_states_has_unique_constraint(self, session):
        """验证 plugin_runtime_states 有唯一约束"""
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                AND table_schema = 'ai'
                AND table_name = 'plugin_runtime_states'
            """)
        )
        # tenant_id + plugin_id 唯一约束
        assert result.scalar() >= 1
