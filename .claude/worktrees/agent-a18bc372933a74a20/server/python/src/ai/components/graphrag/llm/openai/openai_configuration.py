"""OpenAI 配置类定义模块。

本模块定义了 OpenAI LLM 的完整配置结构,包括:
- 核心配置:API 密钥,模型,端点等
- 操作配置:温度,token 限制,响应格式等
- 重试逻辑:超时,重试次数等
- 速率限制:每分钟请求数,并发数等
- 功能标志:模型能力标识
"""

import json
from collections.abc import Hashable
from typing import Any, cast

from ai.components.graphrag.llm.types import LLMConfig


def _non_blank(value: str | None) -> str | None:
    """
    处理non_blank。

    Args:
        value (str | None): value 参数。

    Returns:
        处理结果。
    """
    if value is None:
        return None
    stripped = value.strip()
    return None if stripped == "" else value


class OpenAIConfiguration(Hashable, LLMConfig):
    """
    OpenAI 配置类。

    包含 OpenAI 和 Azure OpenAI 服务所需的所有配置参数。
    实现了 Hashable 接口,可用作字典键或集合元素。
    """

    # 核心配置
    _api_key: str  # API 密钥
    _model: str  # 模型名称

    _api_base: str | None  # API 基础 URL
    _api_version: str | None  # API 版本（Azure 专用）
    _cognitive_services_endpoint: str | None  # 认知服务端点（Azure 专用）
    _deployment_name: str | None  # 部署名称（Azure 专用）
    _organization: str | None  # 组织 ID
    _proxy: str | None  # 代理服务器

    # 操作配置
    _n: int | None  # 生成补全数量
    _temperature: float | None  # 温度参数（控制随机性）
    _frequency_penalty: float | None  # 频率惩罚
    _presence_penalty: float | None  # 存在惩罚
    _top_p: float | None  # 核采样参数
    _max_tokens: int | None  # 最大 token 数
    _response_format: str | None  # 响应格式
    _logit_bias: dict[str, float] | None  # Logit 偏置
    _stop: list[str] | None  # 停止序列

    # 重试逻辑
    _max_retries: int | None  # 最大重试次数
    _max_retry_wait: float | None  # 最大重试等待时间
    _request_timeout: float | None  # 请求超时时间

    # 原始配置对象
    _raw_config: dict

    # 功能标志
    _model_supports_json: bool | None  # 模型是否支持原生 JSON 输出

    # 自定义配置
    _tokens_per_minute: int | None  # 每分钟 token 数限制
    _requests_per_minute: int | None  # 每分钟请求数限制
    _concurrent_requests: int | None  # 并发请求数限制
    _encoding_model: str | None  # 编码模型名称
    _sleep_on_rate_limit_recommendation: bool | None  # 是否遵循速率限制建议等待

    def __init__(
        self,
        config: dict,
    ):
        """
        初始化实例。

        Args:
            config (dict): config 参数。

        Returns:
            处理结果。
        """

        def lookup_required(key: str) -> str:
            """查找必需的字符串配置项."""
            return cast("str", config.get(key))

        def lookup_str(key: str) -> str | None:
            """查找可选的字符串配置项."""
            return cast("str | None", config.get(key))

        def lookup_int(key: str) -> int | None:
            """查找可选的整数配置项."""
            result = config.get(key)
            if result is None:
                return None
            return int(cast("int", result))

        def lookup_float(key: str) -> float | None:
            """查找可选的浮点数配置项."""
            result = config.get(key)
            if result is None:
                return None
            return float(cast("float", result))

        def lookup_dict(key: str) -> dict | None:
            """查找可选的字典配置项."""
            return cast("dict | None", config.get(key))

        def lookup_list(key: str) -> list | None:
            """查找可选的列表配置项."""
            return cast("list | None", config.get(key))

        def lookup_bool(key: str) -> bool | None:
            """
            查找可选的布尔配置项。

            支持字符串 "TRUE"/"FALSE",整数 1/0 和原生布尔值。
            """
            value = config.get(key)
            if isinstance(value, str):
                return value.upper() == "TRUE"
            if isinstance(value, int):
                return value > 0
            return cast("bool | None", config.get(key))

        self._api_key = lookup_required("api_key")
        self._model = lookup_required("model")
        self._deployment_name = lookup_str("deployment_name")
        self._api_base = lookup_str("api_base")
        self._api_version = lookup_str("api_version")
        self._cognitive_services_endpoint = lookup_str("cognitive_services_endpoint")
        self._organization = lookup_str("organization")
        self._proxy = lookup_str("proxy")
        self._n = lookup_int("n")
        self._temperature = lookup_float("temperature")
        self._frequency_penalty = lookup_float("frequency_penalty")
        self._presence_penalty = lookup_float("presence_penalty")
        self._top_p = lookup_float("top_p")
        self._max_tokens = lookup_int("max_tokens")
        self._response_format = lookup_str("response_format")
        self._logit_bias = lookup_dict("logit_bias")
        self._stop = lookup_list("stop")
        self._max_retries = lookup_int("max_retries")
        self._request_timeout = lookup_float("request_timeout")
        self._model_supports_json = lookup_bool("model_supports_json")
        self._tokens_per_minute = lookup_int("tokens_per_minute")
        self._requests_per_minute = lookup_int("requests_per_minute")
        self._concurrent_requests = lookup_int("concurrent_requests")
        self._encoding_model = lookup_str("encoding_model")
        self._max_retry_wait = lookup_float("max_retry_wait")
        self._sleep_on_rate_limit_recommendation = lookup_bool(
            "sleep_on_rate_limit_recommendation"
        )
        self._raw_config = config

    @property
    def api_key(self) -> str:
        """获取 API 密钥."""
        return self._api_key

    @property
    def model(self) -> str:
        """获取模型名称."""
        return self._model

    @property
    def deployment_name(self) -> str | None:
        """获取部署名称(Azure OpenAI 专用)."""
        return _non_blank(self._deployment_name)

    @property
    def api_base(self) -> str | None:
        """
        获取 API 基础 URL。

        自动移除尾部斜杠以保持一致性。
        """
        result = _non_blank(self._api_base)
        # 移除尾部斜杠
        return result[:-1] if result and result.endswith("/") else result

    @property
    def api_version(self) -> str | None:
        """获取 API 版本(Azure OpenAI 专用)."""
        return _non_blank(self._api_version)

    @property
    def cognitive_services_endpoint(self) -> str | None:
        """获取认知服务端点(Azure OpenAI 专用)."""
        return _non_blank(self._cognitive_services_endpoint)

    @property
    def organization(self) -> str | None:
        """获取组织 ID."""
        return _non_blank(self._organization)

    @property
    def proxy(self) -> str | None:
        """获取代理服务器地址."""
        return _non_blank(self._proxy)

    @property
    def n(self) -> int | None:
        """获取生成补全的数量."""
        return self._n

    @property
    def temperature(self) -> float | None:
        """获取温度参数(控制输出随机性,0-2 之间)."""
        return self._temperature

    @property
    def frequency_penalty(self) -> float | None:
        """获取频率惩罚参数(降低重复内容,-2.0 到 2.0 之间)."""
        return self._frequency_penalty

    @property
    def presence_penalty(self) -> float | None:
        """获取存在惩罚参数(增加话题多样性,-2.0 到 2.0 之间)."""
        return self._presence_penalty

    @property
    def top_p(self) -> float | None:
        """获取核采样参数(控制生成多样性,0-1 之间)."""
        return self._top_p

    @property
    def max_tokens(self) -> int | None:
        """获取最大 token 数限制."""
        return self._max_tokens

    @property
    def response_format(self) -> str | None:
        """获取响应格式配置."""
        return _non_blank(self._response_format)

    @property
    def logit_bias(self) -> dict[str, float] | None:
        """获取 logit 偏置配置(调整特定 token 的生成概率)."""
        return self._logit_bias

    @property
    def stop(self) -> list[str] | None:
        """获取停止序列列表(遇到这些序列时停止生成)."""
        return self._stop

    @property
    def max_retries(self) -> int | None:
        """获取最大重试次数."""
        return self._max_retries

    @property
    def max_retry_wait(self) -> float | None:
        """获取最大重试等待时间(秒)."""
        return self._max_retry_wait

    @property
    def request_timeout(self) -> float | None:
        """获取请求超时时间(秒)."""
        return self._request_timeout

    @property
    def model_supports_json(self) -> bool | None:
        """获取模型是否支持原生 JSON 输出."""
        return self._model_supports_json

    @property
    def tokens_per_minute(self) -> int | None:
        """获取每分钟 token 数限制."""
        return self._tokens_per_minute

    @property
    def requests_per_minute(self) -> int | None:
        """获取每分钟请求数限制."""
        return self._requests_per_minute

    @property
    def concurrent_requests(self) -> int | None:
        """获取并发请求数限制."""
        return self._concurrent_requests

    @property
    def encoding_model(self) -> str | None:
        """获取编码模型名称(用于 token 计数)."""
        return _non_blank(self._encoding_model)

    @property
    def sleep_on_rate_limit_recommendation(self) -> bool | None:
        """获取是否在收到 429 错误时按建议等待(Azure 专用)."""
        return self._sleep_on_rate_limit_recommendation

    @property
    def raw_config(self) -> dict:
        """获取原始配置字典."""
        return self._raw_config

    def lookup(self, name: str, default_value: Any = None) -> Any:
        """
        处理lookup。

        Args:
            name (str): name 参数。
            default_value (Any): default_value 参数。

        Returns:
            处理结果。
        """
        return self._raw_config.get(name, default_value)

    def __str__(self) -> str:
        """返回配置的字符串表示(格式化 JSON)."""
        return json.dumps(self.raw_config, indent=4, ensure_ascii=False)

    def __repr__(self) -> str:
        """返回配置的调试字符串表示."""
        return f"OpenAIConfiguration({self._raw_config})"

    def __eq__(self, other: object) -> bool:
        """比较两个配置对象是否相等."""
        if not isinstance(other, OpenAIConfiguration):
            return False
        return self._raw_config == other._raw_config

    def __hash__(self) -> int:
        """计算配置对象的哈希值."""
        return hash(tuple(sorted(self._raw_config.items())))
