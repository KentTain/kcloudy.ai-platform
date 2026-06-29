"""
审计日志 API 集成测试
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from iam.models import AuditLog
from iam.models.enums import AuditLogBusinessType, AuditLogOperationType, AuditLogResourceType


@pytest.mark.integration
@pytest.mark.api
class TestAuditLogAPI:
    """审计日志 API 测试"""

    @pytest.mark.asyncio
    async def test_list_audit_logs_success(
        self,
        async_client: AsyncClient,
        test_tenant_id: str,
        auth_headers: dict,
    ):
        """
        场景：成功获取审计日志列表
        WHEN: 发送 GET /iam/admin/v1/audit-logs
        THEN: 返回 200 和审计日志列表
        """
        response = await async_client.get(
            "/iam/admin/v1/audit-logs",
            headers=auth_headers,
            params={"page": 1, "page_size": 20},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_audit_logs_with_filter(
        self,
        async_client: AsyncClient,
        test_tenant_id: str,
        auth_headers: dict,
        session,
    ):
        """
        场景：带筛选条件获取审计日志列表
        WHEN: 发送 GET /iam/admin/v1/audit-logs 带筛选参数
        THEN: 返回匹配的审计日志
        """
        # 创建测试审计日志
        log = AuditLog(
            id=str(uuid.uuid4()),
            tenant_id=test_tenant_id,
            business_domain=AuditLogBusinessType.USER,
            operator_by=str(uuid.uuid4()),
            operator_name="test_user",
            operated_at=datetime.now(timezone.utc),
            operation_type=AuditLogOperationType.USER_CREATE,
            resource_type=AuditLogResourceType.USER,
            resource_name="Test User",
        )
        session.add(log)
        await session.commit()

        response = await async_client.get(
            "/iam/admin/v1/audit-logs",
            headers=auth_headers,
            params={
                "page": 1,
                "page_size": 20,
                "business_domain": AuditLogBusinessType.USER,
                "time_range": "7d",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_audit_options_success(
        self,
        async_client: AsyncClient,
        test_tenant_id: str,
        auth_headers: dict,
        session,
    ):
        """
        场景：成功获取审计日志选项
        WHEN: 发送 GET /iam/admin/v1/audit-logs/options
        THEN: 返回 200 和审计选项
        """
        # 创建测试审计日志（确保有选项数据）
        log = AuditLog(
            id=str(uuid.uuid4()),
            tenant_id=test_tenant_id,
            business_domain=AuditLogBusinessType.USER,
            operator_by=str(uuid.uuid4()),
            operator_name="test_user",
            operated_at=datetime.now(timezone.utc),
            operation_type=AuditLogOperationType.USER_CREATE,
            resource_type=AuditLogResourceType.USER,
            resource_name="Test User",
        )
        session.add(log)
        await session.commit()

        response = await async_client.get(
            "/iam/admin/v1/audit-logs/options",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "business_domains" in data["data"]
        assert "actions" in data["data"]
        assert "resource_types" in data["data"]

    @pytest.mark.asyncio
    async def test_list_audit_logs_unauthorized(self, async_client: AsyncClient):
        """
        场景：未授权访问审计日志列表
        WHEN: 发送 GET /iam/admin/v1/audit-logs 无认证
        THEN: 返回 401
        """
        response = await async_client.get(
            "/iam/admin/v1/audit-logs",
            params={"page": 1, "page_size": 20},
        )

        assert response.status_code == 401
