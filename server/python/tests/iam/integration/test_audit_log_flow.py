"""
审计日志 API 集成测试

需要后端服务运行才能执行。
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from iam.models import AuditLog


# =============================================================================
# 集成测试需要后端服务运行，使用 conftest 提供的 fixtures
# 参考：tests/iam/conftest.py
# =============================================================================


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
    ):
        """
        场景：按用户名过滤审计日志列表
        WHEN: 发送 GET /iam/admin/v1/audit-logs?user_name=admin
        THEN: 返回 200 和过滤后的结果
        """
        response = await async_client.get(
            "/iam/admin/v1/audit-logs",
            headers=auth_headers,
            params={"page": 1, "page_size": 20, "user_name": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data

    @pytest.mark.asyncio
    async def test_get_audit_options_success(
        self,
        async_client: AsyncClient,
        test_tenant_id: str,
        auth_headers: dict,
    ):
        """
        场景：获取审计日志筛选选项
        WHEN: 发送 GET /iam/admin/v1/audit-logs/options
        THEN: 返回 200 和可用的筛选选项
        """
        response = await async_client.get(
            "/iam/admin/v1/audit-logs/options",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

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
