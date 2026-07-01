"""测试 AuditService"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.context import AuditContext
from framework.audit.service import AuditService


@pytest.mark.asyncio
async def test_audit_service_record():
    """测试审计服务记录日志"""
    # Mock session
    session = AsyncMock(spec=AsyncSession)

    # Mock context
    context = AuditContext(
        module="iam",
        resource="user",
        action="create",
        resource_id="user-123",
        resource_name="张三",
        after_data={"id": "user-123", "name": "张三"},
    )

    # Mock 上下文函数
    with patch("framework.audit.service.get_user_id") as mock_get_user_id, \
         patch("framework.audit.service.get_user_name") as mock_get_user_name, \
         patch("framework.audit.service.get_tenant_id") as mock_get_tenant_id, \
         patch("framework.audit.service.get_permission_code") as mock_get_permission_code:

        mock_get_user_id.return_value = "admin-123"
        mock_get_user_name.return_value = "管理员"
        mock_get_tenant_id.return_value = "tenant-123"
        mock_get_permission_code.return_value = "iam:user:create"

        # 执行
        service = AuditService()
        await service.record(session, context)

        # 验证
        session.add.assert_called_once()
        audit_log = session.add.call_args[0][0]

        assert audit_log.tenant_id == "tenant-123"
        assert audit_log.business_domain == "iam"
        assert audit_log.operation_type == "create"
        assert audit_log.resource_type == "user"
        assert audit_log.resource_id == "user-123"
        assert audit_log.resource_name == "张三"
        assert audit_log.permission_code == "iam:user:create"
        assert audit_log.operator_by == "admin-123"
        assert audit_log.operator_name == "管理员"
        assert audit_log.after_data == {"id": "user-123", "name": "张三"}
        assert audit_log.detail["text"] is not None
