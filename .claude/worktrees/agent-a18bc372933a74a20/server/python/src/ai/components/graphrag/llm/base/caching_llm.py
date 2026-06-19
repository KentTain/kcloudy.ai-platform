"""
用于与缓存交互的 LLM 装饰器类

提供了为 LLM 添加缓存功能的装饰器实现。
"""

import json
from typing import Generic, TypeVar, Unpack

from ai.components.graphrag.llm.base._create_cache_key import create_hash_key
from ai.components.graphrag.llm.types import (
    LLM,
    LLMCache,
    LLMInput,
    LLMOutput,
    OnCacheActionFn,
)

# 如果缓存内容有重大变更,应该递增此版本号以使现有缓存失效
_cache_strategy_version = 2


def _noop_cache_fn(_k: str, _v: str | None):
    """空操作的缓存回调函数"""


TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class CachingLLM(LLM[TIn, TOut], Generic[TIn, TOut]):
    """
    用于与缓存交互的 LLM 装饰器类

    为 LLM 添加缓存功能,可以缓存 LLM 的调用结果,避免重复调用相同的请求。
    支持缓存命中和缓存未命中的回调函数。
    """

    _cache: LLMCache
    _delegate: LLM[TIn, TOut]
    _operation: str
    _llm_parameters: dict
    _on_cache_hit: OnCacheActionFn
    _on_cache_miss: OnCacheActionFn

    def __init__(
        self,
        delegate: LLM[TIn, TOut],
        llm_parameters: dict,
        operation: str,
        cache: LLMCache,
    ):
        """
        初始化缓存 LLM

        Args:
            delegate: 被装饰的 LLM 实例
            llm_parameters: LLM 参数字典
            operation: 操作类型(如 'chat', 'completion' 等)
            cache: 缓存实例
        """
        self._delegate = delegate
        self._llm_parameters = llm_parameters
        self._cache = cache
        self._operation = operation
        self._on_cache_hit = _noop_cache_fn
        self._on_cache_miss = _noop_cache_fn

    def set_delegate(self, delegate: LLM[TIn, TOut]) -> None:
        """
        设置委托的 LLM(用于测试)

        Args:
            delegate: 新的 LLM 实例
        """
        self._delegate = delegate

    def on_cache_hit(self, fn: OnCacheActionFn | None) -> None:
        """
        设置缓存命中时的回调函数

        Args:
            fn: 缓存命中回调函数,接收缓存键和名称作为参数
        """
        self._on_cache_hit = fn or _noop_cache_fn

    def on_cache_miss(self, fn: OnCacheActionFn | None) -> None:
        """
        设置缓存未命中时的回调函数

        Args:
            fn: 缓存未命中回调函数,接收缓存键和名称作为参数
        """
        self._on_cache_miss = fn or _noop_cache_fn

    def _cache_key(
        self, input: TIn, name: str | None, args: dict, history: list[dict] | None
    ) -> str:
        """
        生成缓存键

        Args:
            input: 输入数据
            name: 操作名称(可选)
            args: 参数字典
            history: 对话历史记录(可选)

        Returns
        -------
            缓存键字符串
        """
        json_input = json.dumps(input, ensure_ascii=False)
        tag = (
            f"{name}-{self._operation}-v{_cache_strategy_version}"
            if name is not None
            else self._operation
        )
        return create_hash_key(tag, json_input, args, history)

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """
        执行 LLM 调用(带缓存)

        首先检查缓存,如果缓存命中则直接返回缓存结果,
        否则调用实际的 LLM 并将结果存入缓存。

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 输出结果的包装对象
        """
        # 检查是否存在缓存项
        name = kwargs.get("name")
        history_in = kwargs.get("history") or None
        llm_args = {**self._llm_parameters, **(kwargs.get("model_parameters") or {})}
        cache_key = self._cache_key(input, name, llm_args, history_in)
        cached_result = await self._cache.get(cache_key)

        if cached_result:
            # 缓存命中
            self._on_cache_hit(cache_key, name)
            return LLMOutput(
                output=cached_result,
            )

        # 报告缓存未命中
        self._on_cache_miss(cache_key, name)

        # 计算新结果
        result = await self._delegate(input, **kwargs)

        # 缓存新结果
        if result.output is not None:
            await self._cache.set(
                cache_key,
                result.output,
                {
                    "input": input,
                    "parameters": llm_args,
                    "history": history_in,
                },
            )
        return result
