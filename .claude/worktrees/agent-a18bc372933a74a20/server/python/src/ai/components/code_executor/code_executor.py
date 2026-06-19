"""代码执行器组件"""

from collections.abc import Mapping
from enum import StrEnum
from threading import Lock
from typing import Any

import httpx
import orjson
from loguru import logger
from pydantic import BaseModel

from framework.configs.settings import get_settings

from ai.components.code_executor.javascript.javascript_transformer import (
    NodeJsTemplateTransformer,
)
from ai.components.code_executor.jinja2.jinja2_transformer import (
    Jinja2TemplateTransformer,
)
from ai.components.code_executor.python3.python3_transformer import (
    Python3TemplateTransformer,
)
from ai.components.code_executor.template_transformer import TemplateTransformer


_logger = logger.bind(name=__name__)


class CodeExecutionError(Exception):
    """代码执行错误"""

    pass


class CodeExecutionResponse(BaseModel):
    """代码执行响应"""

    class Data(BaseModel):
        """响应数据"""

        stdout: str | None = None
        error: str | None = None

    code: int
    message: str
    data: Data


class CodeLanguage(StrEnum):
    """代码语言枚举"""

    PYTHON3 = "python3"
    JINJA2 = "jinja2"
    JAVASCRIPT = "javascript"


class CodeExecutor:
    """代码执行器"""

    dependencies_cache: dict[str, str] = {}
    dependencies_cache_lock = Lock()

    code_template_transformers: dict[CodeLanguage, type[TemplateTransformer]] = {
        CodeLanguage.PYTHON3: Python3TemplateTransformer,
        CodeLanguage.JINJA2: Jinja2TemplateTransformer,
        CodeLanguage.JAVASCRIPT: NodeJsTemplateTransformer,
    }

    code_language_to_running_language = {
        CodeLanguage.JAVASCRIPT: "nodejs",
        CodeLanguage.JINJA2: CodeLanguage.PYTHON3,
        CodeLanguage.PYTHON3: CodeLanguage.PYTHON3,
    }

    supported_dependencies_languages: set[CodeLanguage] = {
        CodeLanguage.PYTHON3,
    }

    @classmethod
    async def execute_code(
        cls, language: CodeLanguage, preload: str, code: str
    ) -> str:
        """
        执行代码

        Args:
            language: 代码语言
            preload: 预加载脚本
            code: 代码

        Returns:
            str: 执行结果
        """

        settings = get_settings()
        url = settings.code_sandbox.endpoint + "/v1/sandbox/run"

        headers = {
            "X-Api-Key": settings.code_sandbox.api_key,
        }

        data = {
            "language": cls.code_language_to_running_language.get(language),
            "code": code,
            "preload": preload,
            "enable_network": True,
        }

        try:
            timeout = httpx.Timeout(
                connect=settings.code_sandbox.connect_timeout,
                read=settings.code_sandbox.read_timeout,
                write=settings.code_sandbox.write_timeout,
                pool=None,
            )

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    str(url),
                    json=data,
                    headers=headers,
                )
            if response.status_code == 503:
                raise CodeExecutionError("Code execution service is unavailable")
            elif response.status_code != 200:
                raise Exception(
                    f"Failed to execute code, got status code {response.status_code},"
                    f" please check if the sandbox service is running",
                )
        except CodeExecutionError as e:
            raise e
        except Exception as e:
            raise CodeExecutionError(
                "Failed to execute code, which is likely a network issue,"
                " please check if the sandbox service is running."
                f" ( Error: {str(e)} )",
            )

        try:
            response_data = orjson.loads(response.content)
        except orjson.JSONDecodeError:
            raise CodeExecutionError("Failed to parse response")

        if (code := response_data.get("code")) != 0:
            raise CodeExecutionError(
                f"Got error code: {code}. Got error msg: {response_data.get('message')}"
            )

        response_code = CodeExecutionResponse(**response_data)

        if response_code.data.error:
            raise CodeExecutionError(response_code.data.error)

        return response_code.data.stdout or ""

    @classmethod
    async def execute_workflow_code_template(
        cls,
        language: CodeLanguage,
        code: str,
        inputs: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """
        执行工作流代码模板

        Args:
            language: 代码语言
            code: 代码
            inputs: 输入

        Returns:
            Mapping[str, Any]: 执行结果
        """

        template_transformer = cls.code_template_transformers.get(language)
        if not template_transformer:
            raise CodeExecutionError(f"Unsupported language {language}")

        runner, preload = template_transformer.transform_caller(code, inputs)

        try:
            response = await cls.execute_code(language, preload, runner)
        except CodeExecutionError as e:
            raise e

        return template_transformer.transform_response(response)
