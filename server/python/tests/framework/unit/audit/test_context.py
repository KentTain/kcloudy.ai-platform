"""测试 AuditContext"""

import pytest
from framework.audit.context import AuditContext


def test_audit_context_creation():
    """测试创建审计上下文"""
    context = AuditContext(
        module="iam",
        resource="user",
        action="create",
        resource_id="user-123",
        resource_name="张三",
    )

    assert context.module == "iam"
    assert context.resource == "user"
    assert context.action == "create"
    assert context.resource_id == "user-123"
    assert context.resource_name == "张三"
    assert context.before_data is None
    assert context.after_data is None
    assert context.detail_extra is None


def test_audit_context_with_data():
    """测试带数据的审计上下文"""
    before_data = {"id": "user-123", "name": "张三"}
    after_data = {"id": "user-123", "name": "李四"}
    detail_extra = {"role": "admin"}

    context = AuditContext(
        module="iam",
        resource="user",
        action="update",
        resource_id="user-123",
        resource_name="李四",
        before_data=before_data,
        after_data=after_data,
        detail_extra=detail_extra,
    )

    assert context.before_data == before_data
    assert context.after_data == after_data
    assert context.detail_extra == detail_extra
