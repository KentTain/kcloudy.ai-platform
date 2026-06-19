"""
Code Executor 导入测试

验证代码执行器组件的模块可以正确导入。

测试覆盖：
- 核心类：CodeExecutor、CodeExecutionError、CodeExecutionResponse、CodeLanguage
- 基类：CodeNodeProvider、TemplateTransformer
- 转换器：Python3TemplateTransformer、NodeJsTemplateTransformer、Jinja2TemplateTransformer
- 代码提供器：Python3CodeProvider、JavascriptCodeProvider
"""

import pytest

from ai.components.code_executor import (
    CodeExecutionError,
    CodeExecutionResponse,
    CodeExecutor,
    CodeLanguage,
    CodeNodeProvider,
    JavascriptCodeProvider,
    Jinja2TemplateTransformer,
    NodeJsTemplateTransformer,
    Python3CodeProvider,
    Python3TemplateTransformer,
    TemplateTransformer,
)


class TestCodeExecutorImports:
    """Code Executor 导入测试"""

    def test_import_code_executor(self):
        """测试导入 CodeExecutor"""
        assert CodeExecutor is not None
        assert isinstance(CodeExecutor, type)

    def test_import_code_execution_error(self):
        """测试导入 CodeExecutionError"""
        assert CodeExecutionError is not None
        assert issubclass(CodeExecutionError, Exception)

    def test_import_code_execution_response(self):
        """测试导入 CodeExecutionResponse"""
        assert CodeExecutionResponse is not None
        assert isinstance(CodeExecutionResponse, type)

        # 验证是 Pydantic 模型
        from pydantic import BaseModel

        assert issubclass(CodeExecutionResponse, BaseModel)

    def test_import_code_language(self):
        """测试导入 CodeLanguage"""
        assert CodeLanguage is not None
        from enum import StrEnum

        assert issubclass(CodeLanguage, StrEnum)


class TestCodeLanguageEnum:
    """CodeLanguage 枚举测试"""

    def test_python3_value(self):
        """测试 PYTHON3 枚举值"""
        assert CodeLanguage.PYTHON3.value == "python3"

    def test_jinja2_value(self):
        """测试 JINJA2 枚举值"""
        assert CodeLanguage.JINJA2.value == "jinja2"

    def test_javascript_value(self):
        """测试 JAVASCRIPT 枚举值"""
        assert CodeLanguage.JAVASCRIPT.value == "javascript"

    def test_all_languages_exist(self):
        """测试所有语言枚举存在"""
        expected_languages = ["PYTHON3", "JINJA2", "JAVASCRIPT"]

        for lang in expected_languages:
            assert hasattr(CodeLanguage, lang), f"缺少语言枚举: {lang}"

    def test_enum_count(self):
        """测试枚举数量"""
        members = list(CodeLanguage)
        assert len(members) == 3


class TestBaseClasses:
    """基类导入测试"""

    def test_import_code_node_provider(self):
        """测试导入 CodeNodeProvider"""
        assert CodeNodeProvider is not None
        assert isinstance(CodeNodeProvider, type)

    def test_import_template_transformer(self):
        """测试导入 TemplateTransformer"""
        assert TemplateTransformer is not None
        assert isinstance(TemplateTransformer, type)


class TestTransformers:
    """转换器导入测试"""

    def test_import_python3_transformer(self):
        """测试导入 Python3TemplateTransformer"""
        assert Python3TemplateTransformer is not None
        assert isinstance(Python3TemplateTransformer, type)
        assert issubclass(Python3TemplateTransformer, TemplateTransformer)

    def test_import_nodejs_transformer(self):
        """测试导入 NodeJsTemplateTransformer"""
        assert NodeJsTemplateTransformer is not None
        assert isinstance(NodeJsTemplateTransformer, type)
        assert issubclass(NodeJsTemplateTransformer, TemplateTransformer)

    def test_import_jinja2_transformer(self):
        """测试导入 Jinja2TemplateTransformer"""
        assert Jinja2TemplateTransformer is not None
        assert isinstance(Jinja2TemplateTransformer, type)
        assert issubclass(Jinja2TemplateTransformer, TemplateTransformer)


class TestCodeProviders:
    """代码提供器导入测试"""

    def test_import_python3_code_provider(self):
        """测试导入 Python3CodeProvider"""
        assert Python3CodeProvider is not None
        assert isinstance(Python3CodeProvider, type)
        assert issubclass(Python3CodeProvider, CodeNodeProvider)

    def test_import_javascript_code_provider(self):
        """测试导入 JavascriptCodeProvider"""
        assert JavascriptCodeProvider is not None
        assert isinstance(JavascriptCodeProvider, type)
        assert issubclass(JavascriptCodeProvider, CodeNodeProvider)


class TestCodeExecutionResponse:
    """CodeExecutionResponse 模型测试"""

    def test_create_response(self):
        """测试创建响应实例"""
        response = CodeExecutionResponse(
            code=200,
            message="success",
            data={"stdout": "hello", "error": None}
        )

        assert response.code == 200
        assert response.message == "success"
        assert response.data.stdout == "hello"
        assert response.data.error is None

    def test_create_error_response(self):
        """测试创建错误响应实例"""
        response = CodeExecutionResponse(
            code=500,
            message="execution failed",
            data={"stdout": None, "error": "SyntaxError"}
        )

        assert response.code == 500
        assert response.message == "execution failed"
        assert response.data.stdout is None
        assert response.data.error == "SyntaxError"


class TestCodeExecutorClassAttributes:
    """CodeExecutor 类属性测试"""

    def test_has_dependencies_cache(self):
        """测试有 dependencies_cache 属性"""
        assert hasattr(CodeExecutor, "dependencies_cache")

    def test_has_code_template_transformers(self):
        """测试有 code_template_transformers 属性"""
        assert hasattr(CodeExecutor, "code_template_transformers")

    def test_transformers_mapping(self):
        """测试转换器映射"""
        transformers = CodeExecutor.code_template_transformers

        assert CodeLanguage.PYTHON3 in transformers
        assert CodeLanguage.JINJA2 in transformers
        assert CodeLanguage.JAVASCRIPT in transformers

        assert transformers[CodeLanguage.PYTHON3] == Python3TemplateTransformer
        assert transformers[CodeLanguage.JINJA2] == Jinja2TemplateTransformer
        assert transformers[CodeLanguage.JAVASCRIPT] == NodeJsTemplateTransformer

    def test_supported_dependencies_languages(self):
        """测试支持依赖安装的语言"""
        supported = CodeExecutor.supported_dependencies_languages

        # 只有 PYTHON3 支持依赖安装
        assert CodeLanguage.PYTHON3 in supported


class TestCodeExecutionError:
    """CodeExecutionError 异常测试"""

    def test_raise_error(self):
        """测试抛出异常"""
        with pytest.raises(CodeExecutionError):
            raise CodeExecutionError("Test error")

    def test_error_message(self):
        """测试异常消息"""
        error = CodeExecutionError("Execution failed")
        assert str(error) == "Execution failed"
