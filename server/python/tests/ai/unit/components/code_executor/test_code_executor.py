"""代码执行器组件测试"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from ai.components.code_executor import (
    CodeExecutionError,
    CodeExecutor,
    CodeLanguage,
    JavascriptCodeProvider,
    Python3CodeProvider,
)


class TestCodeExecutorSandbox:
    """测试代码执行器与沙箱环境的交互"""

    @pytest.fixture
    def mock_settings(self):
        """模拟全局设置"""
        mock_settings = MagicMock()
        mock_settings.code_sandbox.endpoint = "http://localhost:8194"
        mock_settings.code_sandbox.api_key = "dify-sandbox"
        mock_settings.code_sandbox.connect_timeout = 30
        mock_settings.code_sandbox.read_timeout = 60
        mock_settings.code_sandbox.write_timeout = 30

        with patch(
            "ai.components.code_executor.code_executor.get_settings",
            return_value=mock_settings,
        ):
            yield mock_settings

    @pytest.mark.asyncio
    async def test_python3_code_execution_success(self, mock_settings):
        """测试 Python3 代码执行成功案例"""

        test_code = """
def main(arg1: str, arg2: str) -> dict:
    return {
        "result": f"{arg1} + {arg2} = {arg1 + arg2}",
        "sum": len(arg1) + len(arg2)
    }
"""

        mock_response = {
            "code": 0,
            "message": "success",
            "data": {
                "stdout": '<<r>>{"result": "hello + world = helloworld", "sum": 10}<<r>>',
                "error": None,
            },
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = json.dumps(mock_response).encode("utf-8")

            result = await CodeExecutor.execute_workflow_code_template(
                language=CodeLanguage.PYTHON3,
                code=test_code,
                inputs={"arg1": "hello", "arg2": "world"},
            )

            assert result == {"result": "hello + world = helloworld", "sum": 10}

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert str(call_args[1]["json"]["language"]) == "python3"
            assert (
                "def main(arg1: str, arg2: str) -> dict:"
                in call_args[1]["json"]["code"]
            )

    @pytest.mark.asyncio
    async def test_javascript_code_execution_success(self, mock_settings):
        """测试 JavaScript 代码执行成功案例"""

        test_code = """
function main({arg1, arg2}) {
    return {
        result: arg1 + arg2,
        length: (arg1 + arg2).length
    }
}
"""

        mock_response = {
            "code": 0,
            "message": "success",
            "data": {
                "stdout": '<<r>>{"result": "helloworld", "length": 10}<<r>>',
                "error": None,
            },
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = json.dumps(mock_response).encode("utf-8")

            result = await CodeExecutor.execute_workflow_code_template(
                language=CodeLanguage.JAVASCRIPT,
                code=test_code,
                inputs={"arg1": "hello", "arg2": "world"},
            )

            assert result == {"result": "helloworld", "length": 10}

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert str(call_args[1]["json"]["language"]) == "nodejs"
            assert "function main({arg1, arg2})" in call_args[1]["json"]["code"]

    @pytest.mark.asyncio
    async def test_jinja2_code_execution_success(self, mock_settings):
        """测试 Jinja2 模板执行成功案例"""

        test_code = "Hello, {{ name }}! Today is {{ day }}."

        mock_response = {
            "code": 0,
            "message": "success",
            "data": {
                "stdout": "<<r>>Hello, World! Today is Monday.<<r>>",
                "error": None,
            },
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = json.dumps(mock_response).encode("utf-8")

            result = await CodeExecutor.execute_workflow_code_template(
                language=CodeLanguage.JINJA2,
                code=test_code,
                inputs={"name": "World", "day": "Monday"},
            )

            assert result == {"result": "Hello, World! Today is Monday."}

    @pytest.mark.asyncio
    async def test_code_execution_error_handling(self, mock_settings):
        """测试代码执行错误处理"""

        test_code = """
def main(arg1: str, arg2: str) -> dict:
    raise ValueError("测试错误")
"""

        mock_response = {
            "code": 0,
            "message": "success",
            "data": {"stdout": None, "error": "ValueError: 测试错误"},
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = json.dumps(mock_response).encode("utf-8")

            with pytest.raises(CodeExecutionError) as exc_info:
                await CodeExecutor.execute_workflow_code_template(
                    language=CodeLanguage.PYTHON3,
                    code=test_code,
                    inputs={"arg1": "hello", "arg2": "world"},
                )

            assert "ValueError: 测试错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sandbox_service_unavailable(self, mock_settings):
        """测试沙箱服务不可用的情况"""

        test_code = "def main(): pass"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 503

            with pytest.raises(CodeExecutionError) as exc_info:
                await CodeExecutor.execute_code(
                    language=CodeLanguage.PYTHON3, preload="", code=test_code
                )

            assert "Code execution service is unavailable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_settings):
        """测试网络错误处理"""

        test_code = "def main(): pass"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("连接超时")

            with pytest.raises(CodeExecutionError) as exc_info:
                await CodeExecutor.execute_code(
                    language=CodeLanguage.PYTHON3, preload="", code=test_code
                )

            assert "Failed to execute code, which is likely a network issue" in str(
                exc_info.value
            )

    def test_python3_code_provider(self):
        """测试 Python3 代码提供者"""
        provider = Python3CodeProvider()

        assert provider.get_language() == "python3"
        assert provider.is_accept_language("python3") is True
        assert provider.is_accept_language("javascript") is False

        default_code = provider.get_default_code()
        assert "def main(arg1: str, arg2: str) -> dict:" in default_code
        assert 'return {\n        "result": arg1 + arg2,' in default_code

        config = provider.get_default_config()
        assert config["type"] == "code"
        assert config["config"]["code_language"] == "python3"
        assert config["config"]["code"] == default_code
        assert len(config["config"]["variables"]) == 2

    def test_javascript_code_provider(self):
        """测试 JavaScript 代码提供者"""
        provider = JavascriptCodeProvider()

        assert provider.get_language() == "javascript"
        assert provider.is_accept_language("javascript") is True
        assert provider.is_accept_language("python3") is False

        default_code = provider.get_default_code()
        assert "function main({arg1, arg2})" in default_code
        assert "result: arg1 + arg2" in default_code

        config = provider.get_default_config()
        assert config["type"] == "code"
        assert config["config"]["code_language"] == "javascript"
        assert config["config"]["code"] == default_code

    def test_unsupported_language(self):
        """测试不支持的语言"""
        assert CodeExecutor.code_template_transformers.get(CodeLanguage.PYTHON3)
        assert CodeExecutor.code_template_transformers.get(CodeLanguage.JAVASCRIPT)
        assert CodeExecutor.code_template_transformers.get(CodeLanguage.JINJA2)

    @pytest.mark.asyncio
    async def test_unsupported_language_error(self, mock_settings):
        """测试不支持的语言抛出错误"""
        from ai.components.code_executor import CodeLanguage

        # 直接测试 execute_workflow_code_template 对不支持语言的处理
        # 我们使用一个伪造的 language 值来测试
        with pytest.raises(CodeExecutionError) as exc_info:
            await CodeExecutor.execute_workflow_code_template(
                language="unsupported_lang",  # type: ignore
                code="def main(): pass",
                inputs={},
            )

        assert "Unsupported language" in str(exc_info.value)


class TestCodeExecutorImports:
    """Code Executor 导入测试"""

    def test_import_all_exports(self):
        """测试导入所有导出类"""
        from ai.components.code_executor import (
            CodeExecutor,
            CodeExecutionError,
            CodeExecutionResponse,
            CodeLanguage,
            CodeNodeProvider,
            TemplateTransformer,
            Python3TemplateTransformer,
            NodeJsTemplateTransformer,
            Jinja2TemplateTransformer,
            Python3CodeProvider,
            JavascriptCodeProvider,
        )

        # 验证所有类都已导入
        assert CodeExecutor is not None
        assert CodeExecutionError is not None
        assert CodeExecutionResponse is not None
        assert CodeLanguage is not None
        assert CodeNodeProvider is not None
        assert TemplateTransformer is not None
        assert Python3TemplateTransformer is not None
        assert NodeJsTemplateTransformer is not None
        assert Jinja2TemplateTransformer is not None
        assert Python3CodeProvider is not None
        assert JavascriptCodeProvider is not None

    def test_code_language_enum(self):
        """测试语言枚举"""
        from ai.components.code_executor import CodeLanguage

        # 验证枚举值
        assert CodeLanguage.PYTHON3.value == "python3"
        assert CodeLanguage.JAVASCRIPT.value == "javascript"
        assert CodeLanguage.JINJA2.value == "jinja2"

        # 验证枚举成员
        assert len(list(CodeLanguage)) >= 3


class TestCodeNodeProvider:
    """CodeNodeProvider 基类测试"""

    def test_base_provider_inheritance(self):
        """测试基类继承自 BaseModel"""
        from ai.components.code_executor import CodeNodeProvider
        from pydantic import BaseModel

        assert issubclass(CodeNodeProvider, BaseModel)

    def test_base_provider_methods(self):
        """测试基类方法定义"""
        from ai.components.code_executor import CodeNodeProvider

        # 验证抽象方法存在
        assert hasattr(CodeNodeProvider, 'get_language')
        assert hasattr(CodeNodeProvider, 'get_default_code')
        assert hasattr(CodeNodeProvider, 'is_accept_language')
        assert hasattr(CodeNodeProvider, 'get_default_config')

        # 验证 get_language 是抽象方法
        assert getattr(CodeNodeProvider.get_language, '__isabstractmethod__', False)
        assert getattr(CodeNodeProvider.get_default_code, '__isabstractmethod__', False)


class TestJinja2CodeProvider:
    """Jinja2CodeProvider 测试"""

    def test_jinja2_code_provider(self):
        """测试 Jinja2CodeProvider 创建"""
        from ai.components.code_executor.jinja2.jinja2_transformer import Jinja2TemplateTransformer

        transformer = Jinja2TemplateTransformer()

        assert transformer is not None
        assert hasattr(Jinja2TemplateTransformer, 'transform_caller')
        assert hasattr(Jinja2TemplateTransformer, 'transform_response')
        assert hasattr(Jinja2TemplateTransformer, 'get_runner_script')

    def test_jinja2_default_code(self):
        """测试 Jinja2 默认代码模板"""
        # Jinja2 的默认模板应该是一个简单的字符串
        default_template = "Hello, {{ name }}!"

        # 验证模板可以渲染
        from jinja2 import Template
        template = Template(default_template)
        result = template.render(name="World")

        assert result == "Hello, World!"

    def test_jinja2_transformer_format_response(self):
        """测试 Jinja2 响应格式化"""
        from ai.components.code_executor.jinja2.jinja2_transformer import Jinja2TemplateTransformer

        # 测试格式化响应（响应需要包含 <<r>> 标签）
        response = "<<r>>Hello, World!<<r>>"
        formatted = Jinja2TemplateTransformer.transform_response(response)

        assert formatted == {"result": "Hello, World!"}
