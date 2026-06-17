"""代码模板转换器基类"""

import re
from abc import ABC, abstractmethod
from base64 import b64encode
from collections.abc import Mapping
from typing import Any

import orjson


class TemplateTransformer(ABC):
    """模板转换器基类"""

    _code_placeholder: str = "{{code}}"
    _inputs_placeholder: str = "{{inputs}}"
    _result_tag: str = "<<r>>"

    @classmethod
    def transform_caller(cls, code: str, inputs: Mapping[str, Any]) -> tuple[str, str]:
        """
        转换代码为运行器

        Args:
            code: 代码
            inputs: 输入

        Returns:
            (运行器脚本, 预加载脚本)
        """

        runner_script = cls.assemble_runner_script(code, inputs)
        preload_script = cls.get_preload_script()

        return runner_script, preload_script

    @classmethod
    def extract_result_str_from_response(cls, response: str):
        """从响应中提取结果字符串"""
        result = re.search(
            rf"{cls._result_tag}(.*){cls._result_tag}", response, re.DOTALL
        )
        if not result:
            raise ValueError("Failed to parse result")
        return result.group(1)

    @classmethod
    def transform_response(cls, response: str) -> Mapping[str, Any]:
        """
        转换响应为字典

        Args:
            response: 响应

        Returns:
            转换后的字典
        """

        try:
            result = orjson.loads(cls.extract_result_str_from_response(response))
        except orjson.JSONDecodeError:
            raise ValueError("failed to parse response")
        if not isinstance(result, dict):
            raise ValueError("result must be a dict")
        if not all(isinstance(k, str) for k in result):
            raise ValueError("result keys must be strings")
        return result

    @classmethod
    @abstractmethod
    def get_runner_script(cls) -> str:
        """获取运行器脚本"""
        pass

    @classmethod
    def serialize_inputs(cls, inputs: Mapping[str, Any]) -> str:
        """序列化输入"""
        inputs_json_bytes = orjson.dumps(inputs, option=orjson.OPT_NON_STR_KEYS)
        input_base64_encoded = b64encode(inputs_json_bytes).decode("utf-8")
        return input_base64_encoded

    @classmethod
    def assemble_runner_script(cls, code: str, inputs: Mapping[str, Any]) -> str:
        """组装运行器脚本"""
        script = cls.get_runner_script()
        script = script.replace(cls._code_placeholder, code)
        inputs_str = cls.serialize_inputs(inputs)
        script = script.replace(cls._inputs_placeholder, inputs_str)
        return script

    @classmethod
    def get_preload_script(cls) -> str:
        """获取预加载脚本"""
        return ""
