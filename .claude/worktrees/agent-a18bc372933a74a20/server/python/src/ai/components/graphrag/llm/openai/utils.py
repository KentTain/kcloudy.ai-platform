"""OpenAI API 工具函数模块。

本模块提供用于 OpenAI API 调用的各种工具函数,包括:
- Token 计数
- 变量替换
- JSON 解析和修复
- 错误处理
- 缓存参数构建
"""

import json
import logging
from collections.abc import Callable
from typing import Any

import tiktoken
from json_repair import repair_json
from openai import (
    APIConnectionError,
    InternalServerError,
    RateLimitError,
)

from ai.components.graphrag.llm.openai.openai_configuration import OpenAIConfiguration

# 默认编码模型
DEFAULT_ENCODING = "cl100k_base"

# 编码器缓存
_encoders: dict[str, tiktoken.Encoding] = {}

# 可重试的错误类型列表
RETRYABLE_ERRORS: list[type[Exception]] = [
    RateLimitError,
    APIConnectionError,
    InternalServerError,
]

# 速率限制错误类型列表
RATE_LIMIT_ERRORS: list[type[Exception]] = [RateLimitError]

log = logging.getLogger(__name__)


def get_token_counter(config: OpenAIConfiguration) -> Callable[[str], int]:
    """
    获取token_counter。

    Args:
        config (OpenAIConfiguration): config 参数。

    Returns:
        处理结果。
    """
    model = config.encoding_model or "cl100k_base"
    enc = _encoders.get(model)
    if enc is None:
        enc = tiktoken.get_encoding(model)
        _encoders[model] = enc

    return lambda s: len(enc.encode(s))


def perform_variable_replacements(
    input: str, history: list[dict], variables: dict | None
) -> str:
    """
    处理perform_variable_replacements。

    Args:
        input (str): input 参数。
        history (list[dict]): history 参数。
        variables (dict | None): variables 参数。

    Returns:
        处理结果。
    """
    result = input

    def replace_all(input: str) -> str:
        """替换字符串中的所有变量占位符."""
        result = input
        if variables:
            for entry in variables:
                result = result.replace(f"{{{entry}}}", variables[entry])
        return result

    # 替换输入中的变量
    result = replace_all(result)
    # 替换历史记录中系统消息的变量
    for i in range(len(history)):
        entry = history[i]
        if entry.get("role") == "system":
            history[i]["content"] = replace_all(entry.get("content") or "")

    return result


def get_completion_cache_args(configuration: OpenAIConfiguration) -> dict:
    """
    获取completion_cache_args。

    Args:
        configuration (OpenAIConfiguration): configuration 参数。

    Returns:
        处理结果。
    """
    return {
        "model": configuration.model,
        "temperature": configuration.temperature,
        "frequency_penalty": configuration.frequency_penalty,
        "presence_penalty": configuration.presence_penalty,
        "top_p": configuration.top_p,
        "max_tokens": configuration.max_tokens,
        "n": configuration.n,
    }


def get_completion_llm_args(
    parameters: dict | None, configuration: OpenAIConfiguration
) -> dict:
    """
    获取completion_llm_args。

    Args:
        parameters (dict | None): parameters 参数。
        configuration (OpenAIConfiguration): configuration 参数。

    Returns:
        处理结果。
    """
    return {
        **get_completion_cache_args(configuration),
        **(parameters or {}),
    }


def try_parse_json_object(input: str) -> tuple[str, dict]:
    """
    处理try_parse_json_object。

    Args:
        input (str): input 参数。

    Returns:
        处理结果。
    """
    result = None
    try:
        # 首先尝试直接解析
        result = json.loads(input)
    except json.JSONDecodeError:
        log.info("Warning: Error decoding faulty json, attempting repair")

    if result:
        return input, result

    # 清理 JSON 字符串
    input = _clean_up_json(input)

    try:
        result = json.loads(input)
    except json.JSONDecodeError:
        # 使用 json_repair 修复可能格式错误的 JSON 字符串
        input = str(repair_json(json_str=input, return_objects=False))

        # 使用最佳尝试的提示和解析技术生成 JSON 字符串输出
        try:
            result = json.loads(input)
        except json.JSONDecodeError:
            log.exception("error loading json, json=%s", input)
            return input, {}
        else:
            if not isinstance(result, dict):
                log.exception("not expected dict type. type=%s:", type(result))
                return input, {}
            return input, result
    else:
        return input, result


def _clean_up_json(input: str) -> str:
    """
    处理clean_up_json。

    Args:
        input (str): input 参数。

    Returns:
        处理结果。
    """
    # 目前下面的正则判断有问题,此处注释掉
    # _pattern = r"\{(.*)\}"
    # _match = re.search(_pattern, input)
    # input = "{" + _match.group(1) + "}" if _match else input

    # 清理 JSON 字符串
    input = (
        input.replace("{{", "{")
        .replace("}}", "}")
        .replace('"[{', "[{")
        .replace('}]"', "}]")
        .replace("\\", " ")
        .replace("\\n", " ")
        .replace("\n", " ")
        .replace("\r", "")
        .strip()
    )

    # 移除 JSON Markdown 代码块标记
    if input.startswith("```json"):
        input = input[len("```json") :].strip()
    if input.endswith("```"):
        input = input[: len(input) - len("```")].strip()

    return input


def get_sleep_time_from_error(e: Any) -> float:
    """
    获取sleep_time_error。

    Args:
        e (Any): e 参数。

    Returns:
        处理结果。
    """
    sleep_time = 0.0
    if isinstance(e, RateLimitError) and _please_retry_after in str(e):
        # 可能是 "second" 或 "seconds"
        sleep_time = int(str(e).split(_please_retry_after)[1].split(" second")[0])

    return sleep_time


# 速率限制错误消息中的重试提示前缀
_please_retry_after = "Please retry after "
