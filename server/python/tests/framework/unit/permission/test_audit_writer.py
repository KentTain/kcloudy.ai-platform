"""
审计写入辅助单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from framework.permission.audit_writer import write_audit


@pytest.mark.asyncio
class TestAuditWriter:
    """审计写入辅助测试"""

    async def test_write_audit_creates_auditlog(self):
        """写入审计日志创建 AuditLog 记录"""
        session = AsyncMock(spec=AsyncSession)

        with patch("framework.permission.audit_writer.get_tenant_id", return_value="tenant-1"), \
             patch("framework.permission.audit_writer.get_user_id", return_value="user-1"), \
             patch("framework.permission.audit_writer.get_permission_code", return_value="document:library:write"):
            await write_audit(
                session=session,
                business_domain="document",
                operation_type="update_library",
                resource_type="library",
                resource_id="lib-1",
                resource_name="研发文档库",
                before_data={"name": "旧名"},
                after_data={"name": "新名"},
                detail={"type": "update_library_settings"},
            )

        session.add.assert_called_once()
        added_obj = session.add.call_args[0][0]
        assert added_obj.business_domain == "document"
        assert added_obj.operation_type == "update_library"
        assert added_obj.resource_id == "lib-1"
        assert added_obj.tenant_id == "tenant-1"
        assert added_obj.operator_by == "user-1"

    async def test_write_audit_missing_business_domain_raises(self):
        """缺少 business_domain 抛出 ValueError"""
        session = AsyncMock(spec=AsyncSession)
        with pytest.raises(ValueError, match="business_domain"):
            await write_audit(
                session=session,
                business_domain="",
                operation_type="update",
                resource_type="library",
                resource_name="库",
            )

    async def test_write_audit_missing_operation_type_raises(self):
        """缺少 operation_type 抛出 ValueError"""
        session = AsyncMock(spec=AsyncSession)
        with pytest.raises(ValueError, match="operation_type"):
            await write_audit(
                session=session,
                business_domain="document",
                operation_type="",
                resource_type="library",
                resource_name="库",
            )

    async def test_write_audit_missing_resource_type_raises(self):
        """缺少 resource_type 抛出 ValueError"""
        session = AsyncMock(spec=AsyncSession)
        with pytest.raises(ValueError, match="resource_type"):
            await write_audit(
                session=session,
                business_domain="document",
                operation_type="update",
                resource_type="",
                resource_name="库",
            )
