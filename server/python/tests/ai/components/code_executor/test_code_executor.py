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
