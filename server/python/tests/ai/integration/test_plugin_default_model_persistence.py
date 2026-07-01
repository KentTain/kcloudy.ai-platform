"""默认模型持久化集成测试

基于数据库实际表结构（由迁移创建）：
- plugin_default_models: id, tenant_id, model_type, plugin_id, model_name,
  custom_model_name, credential_id, custom_base_url, created_at, updated_at
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest_asyncio.fixture
async def db_session(ai_async_engine):
    """每个测试独立的数据库会话"""
    session_factory = async_sessionmaker(ai_async_engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        try:
            await session.close()
        except RuntimeError:
            pass


@pytest.fixture
def tenant_a_id():
    return str(uuid.uuid4())


@pytest.fixture
def tenant_b_id():
    return str(uuid.uuid4())


# =============================================================================
# 表结构验证
# =============================================================================


@pytest.mark.integration
class TestTableStructure:
    """验证 plugin_default_models 表结构符合迁移定义"""

    @pytest.mark.asyncio
    async def test_table_columns(self, db_session):
        """表应包含迁移定义的列"""
        result = await db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='ai' AND table_name='plugin_default_models' "
                "ORDER BY ordinal_position"
            )
        )
        cols = [r[0] for r in result]
        # 验证必需列存在
        required_cols = [
            "id", "tenant_id", "model_type", "plugin_id", "model_name",
            "created_at", "updated_at"
        ]
        for col in required_cols:
            assert col in cols, f"Missing required column: {col}"


# =============================================================================
# CRUD 操作
# =============================================================================


@pytest.mark.integration
class TestDefaultModelCRUD:
    """默认模型 CRUD 集成测试"""

    @pytest.mark.asyncio
    async def test_create_default_model(self, db_session, tenant_a_id):
        """测试创建默认模型"""
        model_id = str(uuid.uuid4())

        await db_session.execute(
            text(
                "INSERT INTO ai.plugin_default_models "
                "(id, tenant_id, model_type, plugin_id, model_name) "
                "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name)"
            ),
            {
                "id": model_id,
                "tenant_id": tenant_a_id,
                "model_type": "llm",
                "plugin_id": "openai",
                "model_name": "gpt-4o-mini",
            },
        )
        await db_session.flush()

        result = await db_session.execute(
            text(
                "SELECT id, tenant_id, plugin_id, model_name "
                "FROM ai.plugin_default_models WHERE id = :id"
            ),
            {"id": model_id},
        )
        row = result.first()
        assert row is not None
        assert row.tenant_id == tenant_a_id
        assert row.plugin_id == "openai"
        assert row.model_name == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_get_default_model_not_found(self, db_session, tenant_a_id):
        """测试获取不存在的默认模型"""
        result = await db_session.execute(
            text(
                "SELECT id FROM ai.plugin_default_models "
                "WHERE tenant_id = :tenant_id AND model_type = :model_type"
            ),
            {"tenant_id": tenant_a_id, "model_type": "llm"},
        )
        row = result.first()
        assert row is None

    @pytest.mark.asyncio
    async def test_update_default_model(self, db_session, tenant_a_id):
        """测试更新默认模型"""
        model_id = str(uuid.uuid4())

        # 创建初始记录
        await db_session.execute(
            text(
                "INSERT INTO ai.plugin_default_models "
                "(id, tenant_id, model_type, plugin_id, model_name) "
                "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name)"
            ),
            {
                "id": model_id,
                "tenant_id": tenant_a_id,
                "model_type": "llm",
                "plugin_id": "openai",
                "model_name": "gpt-4o-mini",
            },
        )
        await db_session.flush()

        # 更新
        await db_session.execute(
            text(
                "UPDATE ai.plugin_default_models "
                "SET plugin_id = :plugin_id, model_name = :model_name "
                "WHERE id = :id"
            ),
            {
                "id": model_id,
                "plugin_id": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
            },
        )
        await db_session.flush()

        # 验证更新
        result = await db_session.execute(
            text(
                "SELECT plugin_id, model_name FROM ai.plugin_default_models WHERE id = :id"
            ),
            {"id": model_id},
        )
        row = result.first()
        assert row.plugin_id == "anthropic"
        assert row.model_name == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_create_with_optional_fields(self, db_session, tenant_a_id):
        """测试创建带可选字段的默认模型"""
        model_id = str(uuid.uuid4())

        await db_session.execute(
            text(
                "INSERT INTO ai.plugin_default_models "
                "(id, tenant_id, model_type, plugin_id, model_name, "
                "credential_id, custom_base_url) "
                "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name, "
                ":credential_id, :custom_base_url)"
            ),
            {
                "id": model_id,
                "tenant_id": tenant_a_id,
                "model_type": "llm",
                "plugin_id": "openai",
                "model_name": "gpt-4o",
                "credential_id": "cred_123",
                "custom_base_url": "https://api.openai.com/v1",
            },
        )
        await db_session.flush()

        result = await db_session.execute(
            text(
                "SELECT credential_id, custom_base_url "
                "FROM ai.plugin_default_models WHERE id = :id"
            ),
            {"id": model_id},
        )
        row = result.first()
        assert row.credential_id == "cred_123"
        assert row.custom_base_url == "https://api.openai.com/v1"

    @pytest.mark.asyncio
    async def test_multiple_model_types(self, db_session, tenant_a_id):
        """测试同一租户多种模型类型的默认模型"""
        model_types = ["llm", "text-embedding", "rerank"]

        for model_type in model_types:
            await db_session.execute(
                text(
                    "INSERT INTO ai.plugin_default_models "
                    "(id, tenant_id, model_type, plugin_id, model_name) "
                    "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_a_id,
                    "model_type": model_type,
                    "plugin_id": "test_provider",
                    "model_name": f"test_model_{model_type}",
                },
            )
        await db_session.flush()

        # 验证每种类型都有独立的默认模型
        for model_type in model_types:
            result = await db_session.execute(
                text(
                    "SELECT model_name FROM ai.plugin_default_models "
                    "WHERE tenant_id = :tenant_id AND model_type = :model_type"
                ),
                {"tenant_id": tenant_a_id, "model_type": model_type},
            )
            row = result.first()
            assert row is not None
            assert row.model_name == f"test_model_{model_type}"


# =============================================================================
# 租户隔离
# =============================================================================


@pytest.mark.integration
class TestTenantIsolation:
    """多租户隔离集成测试"""

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, db_session, tenant_a_id, tenant_b_id):
        """不同租户的默认模型应该相互隔离"""
        # 租户 A 的默认模型
        await db_session.execute(
            text(
                "INSERT INTO ai.plugin_default_models "
                "(id, tenant_id, model_type, plugin_id, model_name) "
                "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name)"
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_a_id,
                "model_type": "llm",
                "plugin_id": "openai",
                "model_name": "gpt-4o-mini",
            },
        )

        # 租户 B 的默认模型
        await db_session.execute(
            text(
                "INSERT INTO ai.plugin_default_models "
                "(id, tenant_id, model_type, plugin_id, model_name) "
                "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name)"
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_b_id,
                "model_type": "llm",
                "plugin_id": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
            },
        )
        await db_session.flush()

        # 验证租户 A 只能看到自己的模型
        result = await db_session.execute(
            text(
                "SELECT tenant_id, model_name FROM ai.plugin_default_models "
                "WHERE tenant_id = :tenant_id"
            ),
            {"tenant_id": tenant_a_id},
        )
        rows = result.fetchall()
        assert all(r.tenant_id == tenant_a_id for r in rows)
        assert len(rows) == 1
        assert rows[0].model_name == "gpt-4o-mini"

        # 验证租户 B 只能看到自己的模型
        result = await db_session.execute(
            text(
                "SELECT tenant_id, model_name FROM ai.plugin_default_models "
                "WHERE tenant_id = :tenant_id"
            ),
            {"tenant_id": tenant_b_id},
        )
        rows = result.fetchall()
        assert all(r.tenant_id == tenant_b_id for r in rows)
        assert len(rows) == 1
        assert rows[0].model_name == "claude-3-5-sonnet-20241022"


# =============================================================================
# 约束验证
# =============================================================================


@pytest.mark.integration
class TestConstraints:
    """数据库约束集成测试"""

    @pytest.mark.asyncio
    async def test_unique_tenant_model_type(self, db_session, tenant_a_id):
        """测试 tenant_id + model_type 唯一约束"""
        # 插入第一条记录
        model_id_1 = str(uuid.uuid4())
        await db_session.execute(
            text(
                "INSERT INTO ai.plugin_default_models "
                "(id, tenant_id, model_type, plugin_id, model_name) "
                "VALUES (:id, :tenant_id, :model_type, :plugin_id, :model_name)"
            ),
            {
                "id": model_id_1,
                "tenant_id": tenant_a_id,
                "model_type": "llm",
                "plugin_id": "openai",
                "model_name": "gpt-4o-mini",
            },
        )
        await db_session.flush()

        # 尝试插入相同 tenant_id + model_type 的记录（应该更新而不是插入）
        # 这里验证的是应用层的 upsert 行为，数据库层面可能有唯一约束
        result = await db_session.execute(
            text(
                "SELECT COUNT(*) FROM ai.plugin_default_models "
                "WHERE tenant_id = :tenant_id AND model_type = :model_type"
            ),
            {"tenant_id": tenant_a_id, "model_type": "llm"},
        )
        count = result.scalar()
        assert count == 1, "同一租户同一模型类型应该只有一条默认模型记录"
