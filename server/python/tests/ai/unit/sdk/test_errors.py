# SDK errors 单元测试

import pytest

from ai_plugin.sdk.errors.invoke import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)


class TestInvokeError:
    """InvokeError 基类测试"""

    def test_base_class_inherits_from_value_error(self):
        """测试 InvokeError 继承自 ValueError"""
        assert issubclass(InvokeError, ValueError)

    def test_default_description_is_none(self):
        """测试默认 description 为 None"""
        err = InvokeError()

        assert err.description is None

    def test_custom_description(self):
        """测试自定义 description"""
        err = InvokeError(description="Custom error message")

        assert err.description == "Custom error message"

    def test_str_with_description(self):
        """测试带 description 的字符串表示"""
        err = InvokeError(description="Custom error message")

        assert str(err) == "Custom error message"

    def test_str_without_description(self):
        """测试不带 description 的字符串表示（返回类名）"""
        err = InvokeError()

        assert str(err) == "InvokeError"


class TestInvokeConnectionError:
    """InvokeConnectionError 连接错误测试"""

    def test_inherits_from_invoke_error(self):
        """测试继承自 InvokeError"""
        assert issubclass(InvokeConnectionError, InvokeError)

    def test_class_level_default_description(self):
        """测试类级别的默认 description"""
        # 类属性定义在类级别
        assert InvokeConnectionError.description == "连接错误"

    def test_custom_description_overrides_default(self):
        """测试自定义 description 覆盖默认值"""
        err = InvokeConnectionError(description="网络超时")

        assert err.description == "网络超时"
        assert str(err) == "网络超时"

    def test_instance_without_description_uses_class_name(self):
        """测试不带参数实例化时使用类名"""
        err = InvokeConnectionError()

        # 实例化时会覆盖类属性为 None
        assert err.description is None
        assert str(err) == "InvokeConnectionError"


class TestInvokeServerUnavailableError:
    """InvokeServerUnavailableError 服务器不可用错误测试"""

    def test_inherits_from_invoke_error(self):
        """测试继承自 InvokeError"""
        assert issubclass(InvokeServerUnavailableError, InvokeError)

    def test_class_level_default_description(self):
        """测试类级别的默认 description"""
        assert InvokeServerUnavailableError.description == "服务器不可用错误"


class TestInvokeRateLimitError:
    """InvokeRateLimitError 速率限制错误测试"""

    def test_inherits_from_invoke_error(self):
        """测试继承自 InvokeError"""
        assert issubclass(InvokeRateLimitError, InvokeError)

    def test_class_level_default_description(self):
        """测试类级别的默认 description"""
        assert InvokeRateLimitError.description == "速率限制错误"


class TestInvokeAuthorizationError:
    """InvokeAuthorizationError 授权错误测试"""

    def test_inherits_from_invoke_error(self):
        """测试继承自 InvokeError"""
        assert issubclass(InvokeAuthorizationError, InvokeError)

    def test_class_level_default_description(self):
        """测试类级别的默认 description"""
        assert InvokeAuthorizationError.description == "提供的模型凭证不正确，请检查后重试"


class TestInvokeBadRequestError:
    """InvokeBadRequestError 错误请求测试"""

    def test_inherits_from_invoke_error(self):
        """测试继承自 InvokeError"""
        assert issubclass(InvokeBadRequestError, InvokeError)

    def test_class_level_default_description(self):
        """测试类级别的默认 description"""
        assert InvokeBadRequestError.description == "错误请求"


class TestErrorHierarchy:
    """异常继承层次测试"""

    def test_all_errors_inherit_from_invoke_error(self):
        """测试所有错误类都继承自 InvokeError"""
        error_classes = [
            InvokeConnectionError,
            InvokeServerUnavailableError,
            InvokeRateLimitError,
            InvokeAuthorizationError,
            InvokeBadRequestError,
        ]

        for error_class in error_classes:
            assert issubclass(error_class, InvokeError)
            assert issubclass(error_class, ValueError)

    def test_can_catch_all_with_invoke_error(self):
        """测试可以用 InvokeError 捕获所有子类异常"""
        errors_to_raise = [
            InvokeConnectionError(),
            InvokeServerUnavailableError(),
            InvokeRateLimitError(),
            InvokeAuthorizationError(),
            InvokeBadRequestError(),
        ]

        for err in errors_to_raise:
            with pytest.raises(InvokeError):
                raise err
