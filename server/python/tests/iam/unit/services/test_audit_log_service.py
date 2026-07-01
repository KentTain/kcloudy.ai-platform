"""
审计日志服务单元测试
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from iam.models import AuditLog
from iam.services.audit_log_service import audit_log_service

# 测试租户 ID
TEST_TENANT_ID = "test_tenant_audit_log"


def _build_mock_result(scalars_return=None, scalar_return=None, all_return=None):
    """构建 mock 的 execute 返回值

    注意：execute() 返回的是 Result 对象，它本身不是异步的。
    只有 session.execute() 是异步的。
    """
    # Result 对象不是异步的，使用 MagicMock
    mock_result = MagicMock()
    # scalars() 返回 MagicMock，.all() 返回 list
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_return or []
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar.return_value = scalar_return
    # 支持 result.all() 直接调用
    if all_return is not None:
        mock_result.all.return_value = all_return
    return mock_result


@pytest.mark.unit
class TestAuditLogService:
    """审计日志服务测试"""

    @pytest.mark.asyncio
    async def test_list_audit_logs_empty(self, session):
        """
        场景：查询空审计日志列表
        WHEN: 数据库中无审计日志
        THEN: 返回空列表
        """
        # Mock: 空数据集
        session.execute = AsyncMock()
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        session.execute.side_effect = [mock_result_count, mock_result_list]

        logs, total = await audit_log_service.list_audit_logs(
            session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
        )

        assert total == 0
        assert logs == []

    @pytest.mark.asyncio
    async def test_list_audit_logs_with_data(self, session):
        """
        场景：查询审计日志列表
        WHEN: 数据库中有审计日志
        THEN: 返回日志列表
        """
        # Mock: 数据集
        log = AuditLog(
            id="log-001",
            tenant_id=TEST_TENANT_ID,
            business_domain="user",
            operator_by="user-001",
            operator_name="test_user",
            operated_at=datetime.now(timezone.utc),
            operation_type="create",
            resource_type="user",
            resource_name="Test User",
        )

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[log])

        session.execute = AsyncMock(side_effect=[mock_result_count, mock_result_list])

        logs, total = await audit_log_service.list_audit_logs(
            session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
        )

        assert total == 1
        assert len(logs) == 1
        assert logs[0].operator_name == "test_user"

    @pytest.mark.asyncio
    async def test_list_audit_logs_filter_by_business_domain(self, session):
        """
        场景：按业务域筛选审计日志
        WHEN: 指定业务域筛选条件
        THEN: 返回匹配的日志
        """
        log = AuditLog(
            id="log-001",
            tenant_id=TEST_TENANT_ID,
            business_domain="user",
            operator_by="user-001",
            operator_name="user1",
            operated_at=datetime.now(timezone.utc),
            operation_type="create",
            resource_type="user",
            resource_name="User 1",
        )

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[log])

        session.execute = AsyncMock(side_effect=[mock_result_count, mock_result_list])

        logs, total = await audit_log_service.list_audit_logs(
            session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
            business_domain="user",
        )

        assert total == 1
        assert logs[0].business_domain == "user"

    @pytest.mark.asyncio
    async def test_list_audit_logs_filter_by_time_range(self, session):
        """
        场景：按时间范围筛选审计日志
        WHEN: 指定时间范围筛选条件
        THEN: 返回匹配的日志
        """
        now = datetime.now(timezone.utc)
        log = AuditLog(
            id="log-recent",
            tenant_id=TEST_TENANT_ID,
            business_domain="user",
            operator_by="user-001",
            operator_name="user1",
            operated_at=now - timedelta(hours=2),
            operation_type="create",
            resource_type="user",
            resource_name="User 1",
        )

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[log])

        session.execute = AsyncMock(side_effect=[mock_result_count, mock_result_list])

        logs, total = await audit_log_service.list_audit_logs(
            session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
            time_range="24h",
        )

        assert total == 1
        assert logs[0].id == "log-recent"

    @pytest.mark.asyncio
    async def test_list_audit_logs_pagination(self, session):
        """
        场景：分页查询审计日志
        WHEN: 指定分页参数
        THEN: 返回正确的分页数据
        """
        logs_data = []
        for i in range(25):
            log = AuditLog(
                id=f"log-{i:03d}",
                tenant_id=TEST_TENANT_ID,
                business_domain="user",
                operator_by=f"user-{i}",
                operator_name=f"user_{i}",
                operated_at=datetime.now(timezone.utc),
                operation_type="create",
                resource_type="user",
                resource_name=f"User {i}",
            )
            logs_data.append(log)

        mock_result_count = _build_mock_result(scalar_return=25)
        mock_result_page1 = _build_mock_result(scalars_return=logs_data[:10])
        mock_result_count2 = _build_mock_result(scalar_return=25)
        mock_result_page2 = _build_mock_result(scalars_return=logs_data[10:20])
        mock_result_count3 = _build_mock_result(scalar_return=25)
        mock_result_page3 = _build_mock_result(scalars_return=logs_data[20:25])

        session.execute = AsyncMock(side_effect=[
            mock_result_count, mock_result_page1,
            mock_result_count2, mock_result_page2,
            mock_result_count3, mock_result_page3,
        ])

        # 第一页
        logs, total = await audit_log_service.list_audit_logs(
            session, tenant_id=TEST_TENANT_ID, page=1, page_size=10,
        )
        assert total == 25
        assert len(logs) == 10

        # 第二页
        logs, total = await audit_log_service.list_audit_logs(
            session, tenant_id=TEST_TENANT_ID, page=2, page_size=10,
        )
        assert total == 25
        assert len(logs) == 10

        # 第三页
        logs, total = await audit_log_service.list_audit_logs(
            session, tenant_id=TEST_TENANT_ID, page=3, page_size=10,
        )
        assert total == 25
        assert len(logs) == 5

    @pytest.mark.asyncio
    async def test_get_audit_options_empty(self, session):
        """
        场景：获取空审计选项
        WHEN: 数据库中无审计日志
        THEN: 返回空选项
        """
        from framework.tenant.context import TenantContext

        TenantContext.set_tenant_id(TEST_TENANT_ID)

        # Mock: 三个 distinct 查询都返回空（使用 .all() 而非 .scalars().all()）
        mock_result = _build_mock_result(all_return=[])
        session.execute = AsyncMock(return_value=mock_result)

        options = await audit_log_service.get_audit_options(session)

        assert options.business_domains == []
        assert options.actions == []
        assert options.resource_types == []

    @pytest.mark.asyncio
    async def test_get_audit_options_with_data(self, session):
        """
        场景：获取审计选项
        WHEN: 数据库中有审计日志
        THEN: 返回动态生成的选项
        """
        from framework.tenant.context import TenantContext

        TenantContext.set_tenant_id(TEST_TENANT_ID)

        # Mock: 三个 distinct 查询（使用 .all() 而非 .scalars().all()）
        business_mock = _build_mock_result(all_return=[("user",)])
        action_mock = _build_mock_result(all_return=[("create",)])
        resource_mock = _build_mock_result(all_return=[("user",)])

        session.execute = AsyncMock(side_effect=[business_mock, action_mock, resource_mock])

        options = await audit_log_service.get_audit_options(session)

        assert len(options.business_domains) == 1
        assert options.business_domains[0].value == "user"
        assert len(options.actions) == 1
        assert options.actions[0].value == "create"
        assert len(options.resource_types) == 1
        assert options.resource_types[0].value == "user"
