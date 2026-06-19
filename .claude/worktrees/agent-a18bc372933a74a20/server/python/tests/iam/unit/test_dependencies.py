"""
IAM 依赖注入测试
"""

import pytest
from fastapi import HTTPException, Request
from iam.dependencies import (
    get_current_user_id,
    get_optional_user_id,
    get_current_tenant_id,
    get_current_session_id,
)
from framework.common.ctx import set_user, set_context, Context, clear_context


class TestGetCurrentUserId:
    """get_current_user_id 测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_returns_user_id_when_present(self):
        """用户 ID 存在时返回"""
        set_user(user_id="user-123")
        request = Request(scope={"type": "http", "state": {}})
        result = get_current_user_id(request)
        assert result == "user-123"

    def test_raises_401_when_user_id_missing(self):
        """用户 ID 不存在时抛出 401"""
        request = Request(scope={"type": "http", "state": {}})
        with pytest.raises(HTTPException) as exc:
            get_current_user_id(request)
        assert exc.value.status_code == 401
        assert exc.value.detail == "未登录"

    def test_raises_401_when_user_id_is_none(self):
        """用户 ID 为 None 时抛出 401"""
        request = Request(scope={"type": "http", "state": {}})
        with pytest.raises(HTTPException) as exc:
            get_current_user_id(request)
        assert exc.value.status_code == 401


class TestGetOptionalUserId:
    """get_optional_user_id 测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_returns_user_id_when_present(self):
        """用户 ID 存在时返回"""
        set_user(user_id="user-456")
        request = Request(scope={"type": "http", "state": {}})
        result = get_optional_user_id(request)
        assert result == "user-456"

    def test_returns_none_when_user_id_missing(self):
        """用户 ID 不存在时返回 None"""
        request = Request(scope={"type": "http", "state": {}})
        result = get_optional_user_id(request)
        assert result is None


class TestGetCurrentTenantId:
    """get_current_tenant_id 测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_returns_tenant_id_when_present(self):
        """租户 ID 存在时返回"""
        set_user(user_id="user-123", tenant_id="tenant-789")
        request = Request(scope={"type": "http", "state": {}})
        result = get_current_tenant_id(request)
        assert result == "tenant-789"

    def test_raises_400_when_tenant_id_missing(self):
        """租户 ID 不存在时抛出 400"""
        request = Request(scope={"type": "http", "state": {}})
        with pytest.raises(HTTPException) as exc:
            get_current_tenant_id(request)
        assert exc.value.status_code == 400
        assert exc.value.detail == "缺少租户上下文"


class TestGetCurrentSessionId:
    """get_current_session_id 测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_returns_session_id_when_present(self):
        """会话 ID 存在时返回"""
        ctx = Context(session_id="session-abc")
        set_context(ctx)
        request = Request(scope={"type": "http", "state": {}})
        result = get_current_session_id(request)
        assert result == "session-abc"

    def test_raises_401_when_session_id_missing(self):
        """会话 ID 不存在时抛出 401"""
        request = Request(scope={"type": "http", "state": {}})
        with pytest.raises(HTTPException) as exc:
            get_current_session_id(request)
        assert exc.value.status_code == 401
