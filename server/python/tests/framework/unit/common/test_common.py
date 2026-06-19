"""
common 模块单元测试
"""

from framework.common.ctx import (
    Context,
    clear_context,
    get_context,
    get_tenant_id,
    get_user_id,
    set_user,
)
from framework.common.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
)
from framework.common.responses import (
    error_response,
    paginated_response,
    success_response,
)


class TestExceptions:
    """异常类测试"""

    def test_unauthorized_error(self):
        """
        场景：未授权异常
        WHEN: 创建 UnauthorizedError
        THEN: 正确设置 code 和 message
        """
        exc = UnauthorizedError("请先登录")
        assert exc.code == 401
        assert exc.message == "请先登录"

    def test_forbidden_error(self):
        """
        场景：禁止访问异常
        WHEN: 创建 ForbiddenError
        THEN: 正确设置 code 和 message
        """
        exc = ForbiddenError()
        assert exc.code == 403
        assert exc.message == "禁止访问"

    def test_not_found_error(self):
        """
        场景：未找到异常
        WHEN: 创建 NotFoundError
        THEN: 正确设置 code 和 message
        """
        exc = NotFoundError("用户不存在")
        assert exc.code == 404
        assert exc.message == "用户不存在"

    def test_bad_request_error_with_data(self):
        """
        场景：请求错误异常带数据
        WHEN: 创建 BadRequestError 并传入 data
        THEN: 正确设置所有属性
        """
        exc = BadRequestError("参数错误", data={"field": "name"})
        assert exc.code == 400
        assert exc.message == "参数错误"
        assert exc.data == {"field": "name"}

    def test_service_unavailable_error(self):
        """
        场景：服务不可用异常
        WHEN: 创建 ServiceUnavailableError
        THEN: 正确设置 code 和 message
        """
        exc = ServiceUnavailableError()
        assert exc.code == 503
        assert exc.message == "服务暂时不可用"


class TestResponses:
    """响应函数测试"""

    def test_success_response(self):
        """
        场景：成功响应
        WHEN: 调用 success_response
        THEN: 返回正确格式
        """
        result = success_response(data={"id": 1})
        assert result["code"] == 0
        assert result["message"] == "success"
        assert result["data"] == {"id": 1}

    def test_success_response_with_message(self):
        """
        场景：成功响应自定义消息
        WHEN: 传入自定义消息
        THEN: 使用自定义消息
        """
        result = success_response(data=None, message="创建成功")
        assert result["code"] == 0
        assert result["message"] == "创建成功"

    def test_error_response(self):
        """
        场景：错误响应
        WHEN: 调用 error_response
        THEN: 返回正确格式
        """
        result = error_response(message="操作失败", code=1001)
        assert result["code"] == 1001
        assert result["message"] == "操作失败"
        assert result["data"] is None

    def test_paginated_response(self):
        """
        场景：分页响应
        WHEN: 调用 paginated_response
        THEN: 返回正确格式
        """
        items = [{"id": 1}, {"id": 2}]
        result = paginated_response(items, total=100, page=1, page_size=10)

        assert result["code"] == 0
        assert result["data"]["items"] == items
        assert result["data"]["pagination"]["total"] == 100
        assert result["data"]["pagination"]["page"] == 1
        assert result["data"]["pagination"]["page_size"] == 10
        assert result["data"]["pagination"]["total_pages"] == 10
        assert result["data"]["pagination"]["has_next"] is True
        assert result["data"]["pagination"]["has_prev"] is False


class TestContext:
    """上下文测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_get_context_creates_new(self):
        """
        场景：获取上下文
        WHEN: 上下文不存在
        THEN: 创建新的空上下文
        """
        ctx = get_context()
        assert isinstance(ctx, Context)
        assert ctx.user_id is None
        assert ctx.tenant_id is None

    def test_set_user(self):
        """
        场景：设置用户
        WHEN: 调用 set_user
        THEN: 上下文中存储用户信息
        """
        set_user(
            user_id="user-123",
            user_name="John",
            tenant_id="tenant-456",
            roles=["admin"]
        )

        assert get_user_id() == "user-123"
        assert get_tenant_id() == "tenant-456"

        ctx = get_context()
        assert ctx.user_name == "John"
        assert ctx.roles == ["admin"]

    def test_clear_context(self):
        """
        场景：清理上下文
        WHEN: 调用 clear_context
        THEN: 上下文被清理
        """
        set_user(user_id="user-123")
        clear_context()

        # 获取新的上下文
        ctx = get_context()
        assert ctx.user_id is None

    def test_context_extra(self):
        """
        场景：额外属性
        WHEN: 设置额外属性
        THEN: 可以获取
        """
        ctx = get_context()
        ctx.set("custom_key", "custom_value")
        assert ctx.get("custom_key") == "custom_value"
        assert ctx.get("nonexistent", "default") == "default"
