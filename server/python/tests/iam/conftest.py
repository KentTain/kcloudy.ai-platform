"""
IAM 模块测试配置

提供 IAM 模块的测试 fixtures：
- 测试租户管理
- 测试用户清理
- Mock 数据库会话（session fixture）
- 集成测试 HTTP 客户端 fixtures
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Mock Session Fixture（单元测试使用）
# =============================================================================


@pytest_asyncio.fixture
def session(postgres_session):
    """
    数据库会话（集成测试使用）。

    这是 postgres_session 的别名，用于 IAM 模块集成测试。
    单元测试请直接使用 mock_session。
    """
    return postgres_session


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


# =============================================================================
# 集成测试 HTTP 客户端 Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def async_client(integration_settings, postgres_available):
    """
    异步 HTTP 客户端 fixture（集成测试使用）。

    需要后端服务运行。
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    from httpx import AsyncClient, ASGITransport
    from application_web import create_app

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(async_client, test_tenant_id, postgres_available):
    """
    认证头 fixture（集成测试使用）。

    通过登录获取有效的 JWT token。
    """
    if not postgres_available:
        pytest.skip("PostgreSQL 服务不可用")

    # 登录获取 token
    response = await async_client.post(
        "/iam/console/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )

    if response.status_code != 200:
        pytest.skip("无法登录获取认证 token")

    data = response.json()
    token = data.get("data", {}).get("access_token")

    return {"Authorization": f"Bearer {token}"}
