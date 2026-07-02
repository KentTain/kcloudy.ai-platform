"""
IAM 模块测试配置

提供 IAM 模块的测试 fixtures：
- 测试租户管理
- 测试用户清理
- Mock 数据库会话（session fixture）
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Mock Session Fixture（单元测试使用）
# =============================================================================


@pytest_asyncio.fixture
def session(mock_session):
    """
    模拟数据库会话（单元测试使用）。

    这是 mock_session 的别名，用于 IAM 模块单元测试。
    """
    return mock_session


# =============================================================================
# 测试数据常量
# =============================================================================

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
TEST_TENANT_CODE = "TEST_TENANT"


# =============================================================================
# 测试租户 Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def test_tenant_id():
    """获取测试租户 ID（session 级别，返回固定值）"""
    return TEST_TENANT_ID


@pytest_asyncio.fixture(scope="function", autouse=True)
async def ensure_test_tenant(postgres_engine, postgres_available):
    """
    确保测试租户存在于数据库中（每个测试自动创建）。

    依赖根 conftest.py 提供的 postgres_engine fixture。
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    # 使用独立的会话创建测试租户，避免干扰测试的 session 事务状态
    async with AsyncSession(bind=postgres_engine) as tmp_session:
        stmt = text("""
            INSERT INTO tenant.tenants (id, name, code, status, created_at, updated_at, settings)
            VALUES (:id, :name, :code, :status, NOW(), NOW(), '{}')
            ON CONFLICT (code) DO NOTHING
        """)
        await tmp_session.execute(stmt, {
            "id": TEST_TENANT_ID,
            "name": "测试租户",
            "code": TEST_TENANT_CODE,
            "status": "active",
        })
        await tmp_session.commit()
    yield


# =============================================================================
# 测试用户 Fixtures
# =============================================================================


@pytest.fixture
def cleanup_users():
    """
    清理测试创建的用户（仅收集 ID，实际清理由测试后处理）。

    用法：
        def test_create_user(cleanup_users):
            cleanup_users.append(user_id)
            # ... 测试逻辑
    """
    created_user_ids = []
    yield created_user_ids
    # 不在这里清理，避免事件循环问题
