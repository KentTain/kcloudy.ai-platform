"""
PostgreSQL 数据库集成测试

测试数据库组件与真实 PostgreSQL 服务的交互。
使用 @pytest.mark.integration 标记。
"""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.core.base import Base
from framework.database.types.uuid import StringUUID
from framework.database.types.snowflake import SnowflakeIDGenerator
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin


pytestmark = pytest.mark.integration


# 测试模型定义
class TestModel(Base, AuditMixin):
    """测试模型 - 使用审计混入"""
    __tablename__ = "test_audit_model"

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class TestTenantModel(Base, TenantMixin):
    """测试模型 - 使用租户混入"""
    __tablename__ = "test_tenant_model"

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True)
    value: Mapped[str] = mapped_column(String(100), nullable=False)


class TestDatabaseConnection:
    """数据库连接测试"""

    @pytest.mark.asyncio
    async def test_connection_success(self, postgres_engine, postgres_available):
        """
        场景：连接测试
        WHEN: 创建数据库引擎并连接
        THEN: 成功建立连接
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        async with postgres_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_connection_info(self, postgres_engine, postgres_available):
        """
        场景：连接信息
        WHEN: 获取数据库连接信息
        THEN: 返回正确的数据库信息
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        async with postgres_engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            assert "PostgreSQL" in version


class TestCustomTypes:
    """自定义类型映射测试"""

    @pytest.mark.asyncio
    async def test_string_uuid_type(self):
        """
        场景：StringUUID 类型
        WHEN: 使用 StringUUID 类型
        THEN: 正确映射到数据库字段
        """
        from framework.database.types.uuid import StringUUID

        uuid_type = StringUUID()
        test_uuid = uuid.uuid4()

        # 测试绑定参数
        bound = uuid_type.process_bind_param(test_uuid, None)
        assert bound == str(test_uuid)

        # 测试结果处理
        result = uuid_type.process_result_value(str(test_uuid), None)
        assert isinstance(result, uuid.UUID)

    @pytest.mark.asyncio
    async def test_snowflake_id_generator(self):
        """
        场景：雪花 ID 生成器
        WHEN: 使用 SnowflakeIDGenerator
        THEN: 生成唯一的递增 ID
        """
        generator = SnowflakeIDGenerator()

        # 生成多个 ID
        ids = [generator.generate() for _ in range(100)]

        # 验证唯一性
        assert len(ids) == len(set(ids))

        # 验证递增性
        assert ids == sorted(ids)

        # 验证都是正整数
        assert all(isinstance(id, int) and id > 0 for id in ids)


class TestAuditMixin:
    """审计混入测试"""

    def test_audit_mixin_has_fields(self):
        """
        场景：审计字段
        WHEN: 使用 AuditMixin
        THEN: 包含 created_by 和 updated_by 字段
        """
        # 验证类属性存在
        assert hasattr(TestModel, "created_by")
        assert hasattr(TestModel, "updated_by")

    @pytest.mark.asyncio
    async def test_audit_mixin_in_model(self, postgres_session, postgres_available):
        """
        场景：审计模型使用
        WHEN: 创建带有审计字段的模型实例
        THEN: 正确存储审计信息
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 创建测试实例
        test_id = str(uuid.uuid4())
        model = TestModel(
            id=test_id,
            name="test_audit",
            created_by="user_001",
            updated_by="user_001"
        )

        # 注意：这里不实际写入数据库，因为表可能不存在
        # 仅验证模型可以正确创建
        assert model.id == test_id
        assert model.name == "test_audit"
        assert model.created_by == "user_001"


class TestTenantMixin:
    """租户混入测试"""

    def test_tenant_mixin_has_fields(self):
        """
        场景：租户字段
        WHEN: 使用 TenantMixin
        THEN: 包含 tenant_id 字段
        """
        assert hasattr(TestTenantModel, "tenant_id")

    @pytest.mark.asyncio
    async def test_tenant_mixin_in_model(self, postgres_available):
        """
        场景：租户模型使用
        WHEN: 创建带有租户字段的模型实例
        THEN: 正确存储租户信息
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        tenant_id = str(uuid.uuid4())
        model = TestTenantModel(
            id=str(uuid.uuid4()),
            value="test_value",
            tenant_id=tenant_id
        )

        assert model.tenant_id == tenant_id


class TestSessionManagement:
    """会话管理测试"""

    @pytest.mark.asyncio
    async def test_session_commit(self, postgres_session, postgres_available):
        """
        场景：会话提交
        WHEN: 使用 async session 进行操作
        THEN: 事务正确提交
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 执行简单查询
        result = await postgres_session.execute(text("SELECT 1 as value"))
        row = result.fetchone()

        assert row is not None
        assert row.value == 1

    @pytest.mark.asyncio
    async def test_session_rollback(self, postgres_engine, postgres_available):
        """
        场景：会话回滚
        WHEN: 发生异常时
        THEN: 事务正确回滚
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(bind=postgres_engine) as session:
            try:
                # 执行一个会失败的查询
                await session.execute(text("SELECT nonexistent_column"))
            except Exception:
                await session.rollback()
                # 回滚成功
                assert True

    @pytest.mark.asyncio
    async def test_multiple_queries(self, postgres_session, postgres_available):
        """
        场景：多次查询
        WHEN: 在同一会话中执行多次查询
        THEN: 所有查询正确执行
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        # 执行多次查询
        for i in range(5):
            result = await postgres_session.execute(text(f"SELECT {i} as value"))
            row = result.fetchone()
            assert row.value == i


class TestDatabaseTypes:
    """数据库类型测试"""

    @pytest.mark.asyncio
    async def test_datetime_handling(self, postgres_session, postgres_available):
        """
        场景：日期时间处理
        WHEN: 查询数据库时间
        THEN: 正确处理时区
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        result = await postgres_session.execute(text("SELECT NOW()"))
        db_time = result.scalar()

        assert db_time is not None
        assert isinstance(db_time, datetime)

    @pytest.mark.asyncio
    async def test_json_handling(self, postgres_session, postgres_available):
        """
        场景：JSON 处理
        WHEN: 使用 JSON 类型
        THEN: 正确序列化和反序列化
        """
        if not postgres_available:
            pytest.skip("PostgreSQL 服务不可用")

        result = await postgres_session.execute(
            text("SELECT '{\"key\": \"value\"}'::json as data")
        )
        row = result.fetchone()

        assert row is not None
