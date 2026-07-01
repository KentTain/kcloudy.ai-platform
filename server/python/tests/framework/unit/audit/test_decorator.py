"""测试 audit_log 装饰器"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.decorator import audit_log


@pytest.mark.asyncio
async def test_audit_log_decorator_simple():
    """测试简单场景的装饰器"""
    # Mock session
    session = AsyncMock(spec=AsyncSession)

    # 定义测试函数
    @audit_log(
        module="iam",
        resource="user",
        action="create",
        resource_id_getter=lambda result: result["id"],
        resource_name_getter=lambda result: result["name"],
    )
    async def create_user(session, user_data):
        return {"id": "user-123", "name": "张三"}

    # Mock 上下文和 AuditService
    with patch("framework.audit.decorator.audit_service") as mock_service:
        mock_service.record = AsyncMock()

        # 执行
        result = await create_user(session, {"name": "张三"})

        # 验证结果
        assert result == {"id": "user-123", "name": "张三"}

        # 验证审计日志被调用
        mock_service.record.assert_called_once()
        call_args = mock_service.record.call_args

        assert call_args[0][0] == session  # session
        context = call_args[0][1]  # context

        assert context.module == "iam"
        assert context.resource == "user"
        assert context.action == "create"
        assert context.resource_id == "user-123"
        assert context.resource_name == "张三"
        assert context.after_data == {"id": "user-123", "name": "张三"}


@pytest.mark.asyncio
async def test_audit_log_decorator_with_before_data():
    """测试带 before_data 的装饰器"""
    # Mock session
    session = AsyncMock(spec=AsyncSession)

    # 定义 before_data_getter
    async def get_before_data(args, kwargs):
        return {"id": "user-123", "name": "旧名字"}

    # 定义测试函数
    @audit_log(
        module="iam",
        resource="user",
        action="update",
        resource_id_getter=lambda result: result["id"],
        resource_name_getter=lambda result: result["name"],
        before_data_getter=get_before_data,
    )
    async def update_user(session, user_id, user_data):
        return {"id": user_id, "name": "新名字"}

    # Mock 上下文和 AuditService
    with patch("framework.audit.decorator.audit_service") as mock_service:
        mock_service.record = AsyncMock()

        # 执行
        result = await update_user(session, "user-123", {"name": "新名字"})

        # 验证审计日志被调用
        mock_service.record.assert_called_once()
        call_args = mock_service.record.call_args
        context = call_args[0][1]

        assert context.before_data == {"id": "user-123", "name": "旧名字"}
        assert context.after_data == {"id": "user-123", "name": "新名字"}
