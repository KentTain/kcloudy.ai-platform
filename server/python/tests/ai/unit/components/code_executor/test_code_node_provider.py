"""
CodeNodeProvider 基类测试

验证代码节点提供者基类的定义和接口。

测试覆盖：
- 基类定义
- 抽象方法
- 默认配置生成
- 子类实现约束
"""


import pytest

from ai.components.code_executor import CodeNodeProvider


class TestCodeNodeProviderBasics:
    """CodeNodeProvider 基础测试"""

    def test_is_pydantic_model(self):
        """验证是 Pydantic 模型"""
        from pydantic import BaseModel

        assert issubclass(CodeNodeProvider, BaseModel)

    def test_has_get_language_method(self):
        """验证有 get_language 方法"""
        assert hasattr(CodeNodeProvider, "get_language")
        assert callable(CodeNodeProvider.get_language)

    def test_has_is_accept_language_method(self):
        """验证有 is_accept_language 方法"""
        assert hasattr(CodeNodeProvider, "is_accept_language")
        assert callable(CodeNodeProvider.is_accept_language)

    def test_has_get_default_code_method(self):
        """验证有 get_default_code 方法"""
        assert hasattr(CodeNodeProvider, "get_default_code")
        assert callable(CodeNodeProvider.get_default_code)

    def test_has_get_default_config_method(self):
        """验证有 get_default_config 方法"""
        assert hasattr(CodeNodeProvider, "get_default_config")
        assert callable(CodeNodeProvider.get_default_config)


class TestCodeNodeProviderAbstractMethods:
    """CodeNodeProvider 抽象方法测试"""

    def test_get_language_is_abstract(self):
        """验证 get_language 是抽象方法"""
        # get_language 是静态方法且是抽象方法
        assert hasattr(CodeNodeProvider.get_language, "__isabstractmethod__")

    def test_get_default_code_is_abstract(self):
        """验证 get_default_code 是抽象方法"""
        # get_default_code 是类方法且是抽象方法
        assert hasattr(CodeNodeProvider.get_default_code, "__isabstractmethod__")

    def test_is_accept_language_is_not_abstract(self):
        """验证 is_accept_language 不是抽象方法"""
        # is_accept_language 有默认实现
        assert not hasattr(CodeNodeProvider.is_accept_language, "__isabstractmethod__")

    def test_get_default_config_is_not_abstract(self):
        """验证 get_default_config 不是抽象方法"""
        # get_default_config 有默认实现
        assert not hasattr(CodeNodeProvider.get_default_config, "__isabstractmethod__")


class TestCodeNodeProviderImplementation:
    """CodeNodeProvider 实现约束测试"""

    def test_incomplete_implementation_raises_error(self):
        """验证不完整的实现会引发错误"""

        class IncompleteProvider(CodeNodeProvider):
            """不完整的实现"""
            pass

        # Pydantic BaseModel 会阻止实例化不完整的实现
        with pytest.raises(TypeError) as exc_info:
            IncompleteProvider()

        assert "abstract methods" in str(exc_info.value)

    def test_complete_implementation_can_use(self):
        """验证完整实现可以使用"""

        class CompleteProvider(CodeNodeProvider):
            """完整实现"""

            @staticmethod
            def get_language() -> str:
                return "test_language"

            @classmethod
            def get_default_code(cls) -> str:
                return "print('hello')"

        # 验证方法可用
        assert CompleteProvider.get_language() == "test_language"
        assert CompleteProvider.get_default_code() == "print('hello')"


class TestCodeNodeProviderDefaultConfig:
    """CodeNodeProvider 默认配置测试"""

    def test_default_config_structure(self):
        """测试默认配置结构"""

        class TestProvider(CodeNodeProvider):
            """测试提供者"""

            @staticmethod
            def get_language() -> str:
                return "test"

            @classmethod
            def get_default_code(cls) -> str:
                return "# test code"

        config = TestProvider.get_default_config()

        # 验证配置结构
        assert "type" in config
        assert config["type"] == "code"
        assert "config" in config

        # 验证 config 内容
        config_inner = config["config"]
        assert "variables" in config_inner
        assert "code_language" in config_inner
        assert "code" in config_inner
        assert "outputs" in config_inner

        # 验证语言和代码
        assert config_inner["code_language"] == "test"
        assert config_inner["code"] == "# test code"

    def test_default_config_variables(self):
        """测试默认配置的变量"""

        class TestProvider(CodeNodeProvider):
            """测试提供者"""

            @staticmethod
            def get_language() -> str:
                return "test"

            @classmethod
            def get_default_code(cls) -> str:
                return "# test code"

        config = TestProvider.get_default_config()
        variables = config["config"]["variables"]

        # 默认有两个变量
        assert len(variables) == 2
        assert variables[0]["variable"] == "arg1"
        assert variables[1]["variable"] == "arg2"

    def test_default_config_outputs(self):
        """测试默认配置的输出"""

        class TestProvider(CodeNodeProvider):
            """测试提供者"""

            @staticmethod
            def get_language() -> str:
                return "test"

            @classmethod
            def get_default_code(cls) -> str:
                return "# test code"

        config = TestProvider.get_default_config()
        outputs = config["config"]["outputs"]

        # 默认有 result 输出
        assert "result" in outputs
        assert outputs["result"]["type"] == "string"


class TestCodeNodeProviderIsAcceptLanguage:
    """CodeNodeProvider is_accept_language 方法测试"""

    def test_is_accept_language_true(self):
        """测试接受正确语言"""

        class TestProvider(CodeNodeProvider):
            """测试提供者"""

            @staticmethod
            def get_language() -> str:
                return "python3"

            @classmethod
            def get_default_code(cls) -> str:
                return "# python code"

        assert TestProvider.is_accept_language("python3") is True

    def test_is_accept_language_false(self):
        """测试不接受错误语言"""

        class TestProvider(CodeNodeProvider):
            """测试提供者"""

            @staticmethod
            def get_language() -> str:
                return "python3"

            @classmethod
            def get_default_code(cls) -> str:
                return "# python code"

        assert TestProvider.is_accept_language("javascript") is False

    def test_is_accept_language_case_sensitive(self):
        """测试语言匹配区分大小写"""

        class TestProvider(CodeNodeProvider):
            """测试提供者"""

            @staticmethod
            def get_language() -> str:
                return "Python3"

            @classmethod
            def get_default_code(cls) -> str:
                return "# python code"

        # 语言匹配区分大小写
        assert TestProvider.is_accept_language("Python3") is True
        assert TestProvider.is_accept_language("python3") is False


class TestCodeNodeProviderInheritance:
    """CodeNodeProvider 继承测试"""

    def test_python3_provider_inherits(self):
        """测试 Python3CodeProvider 继承自 CodeNodeProvider"""
        from ai.components.code_executor import Python3CodeProvider

        assert issubclass(Python3CodeProvider, CodeNodeProvider)

    def test_javascript_provider_inherits(self):
        """测试 JavascriptCodeProvider 继承自 CodeNodeProvider"""
        from ai.components.code_executor import JavascriptCodeProvider

        assert issubclass(JavascriptCodeProvider, CodeNodeProvider)

    def test_python3_provider_implements_abstract_methods(self):
        """测试 Python3CodeProvider 实现了抽象方法"""
        from ai.components.code_executor import Python3CodeProvider

        # 应该可以调用这些方法
        language = Python3CodeProvider.get_language()
        assert language == "python3"

        code = Python3CodeProvider.get_default_code()
        assert isinstance(code, str)
        assert len(code) > 0

    def test_javascript_provider_implements_abstract_methods(self):
        """测试 JavascriptCodeProvider 实现了抽象方法"""
        from ai.components.code_executor import JavascriptCodeProvider

        # 应该可以调用这些方法
        language = JavascriptCodeProvider.get_language()
        assert language == "javascript"

        code = JavascriptCodeProvider.get_default_code()
        assert isinstance(code, str)
        assert len(code) > 0
