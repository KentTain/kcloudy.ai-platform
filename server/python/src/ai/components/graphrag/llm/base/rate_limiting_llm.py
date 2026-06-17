"""
速率限制 LLM 实现

提供了为 LLM 添加速率限制,重试机制和并发控制的装饰器实现。
"""

import asyncio
import logging
import threading
from collections.abc import Callable
from typing import Any, Generic, TypeVar, Unpack

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ai.components.graphrag.llm.errors import RetriesExhaustedError
from ai.components.graphrag.llm.limiting import LLMLimiter
from ai.components.graphrag.llm.types import (
    LLM,
    LLMConfig,
    LLMInput,
    LLMInvocationFn,
    LLMInvocationResult,
    LLMOutput,
)

# 速率限制错误类型泛型变量
TRateLimitError = TypeVar("TRateLimitError", bound=BaseException)

# LLM 输入输出类型泛型变量
TIn = TypeVar("TIn")
TOut = TypeVar("TOut")

# 错误消息常量
_CANNOT_MEASURE_INPUT_TOKENS_MSG = "cannot measure input tokens"
_CANNOT_MEASURE_OUTPUT_TOKENS_MSG = "cannot measure output tokens"

log = logging.getLogger(__name__)


def _get_task_factory():
    """延迟导入 task_factory，避免启动时加载 webserver 模块."""
    from ai.components.graphrag.webserver.task.task import task_factory

    return task_factory


def _get_task_stop_error():
    """延迟导入 TaskStopError，避免启动时加载 webserver 模块."""
    from ai.components.graphrag.webserver.task.task_exception import TaskStopError

    return TaskStopError


class RateLimitingLLM(LLM[TIn, TOut], Generic[TIn, TOut]):
    """
    速率限制 LLM 装饰器类

    为 LLM 添加以下功能:
    - 速率限制:控制 token 使用速率(TPM/RPM)
    - 重试机制:自动重试失败的请求
    - 并发控制:使用信号量限制并发请求数
    - 性能监控:记录调用时间和 token 使用情况
    - 任务状态检查:支持任务取消和停止
    """

    _delegate: LLM[TIn, TOut]
    _rate_limiter: LLMLimiter | None
    _semaphore: asyncio.Semaphore | None
    _count_tokens: Callable[[str], int]
    _config: LLMConfig
    _operation: str
    _retryable_errors: list[type[Exception]]
    _rate_limit_errors: list[type[Exception]]
    _on_invoke: LLMInvocationFn
    _extract_sleep_recommendation: Callable[[Any], float]

    def __init__(
        self,
        delegate: LLM[TIn, TOut],
        config: LLMConfig,
        operation: str,
        retryable_errors: list[type[Exception]],
        rate_limit_errors: list[type[Exception]],
        rate_limiter: LLMLimiter | None = None,
        semaphore: asyncio.Semaphore | None = None,
        count_tokens: Callable[[str], int] | None = None,
        get_sleep_time: Callable[[BaseException], float] | None = None,
    ):
        """
        初始化速率限制 LLM

        Args:
            delegate: 被装饰的 LLM 实例
            config: LLM 配置对象
            operation: 操作类型(如 'chat', 'completion' 等)
            retryable_errors: 可重试的异常类型列表
            rate_limit_errors: 速率限制异常类型列表
            rate_limiter: 速率限制器(可选)
            semaphore: 并发控制信号量(可选)
            count_tokens: token 计数函数(可选)
            get_sleep_time: 从异常中提取建议睡眠时间的函数(可选)
        """
        self._delegate = delegate
        self._rate_limiter = rate_limiter
        self._semaphore = semaphore
        self._config = config
        self._operation = operation
        self._retryable_errors = retryable_errors
        self._rate_limit_errors = rate_limit_errors
        self._count_tokens = count_tokens or (lambda _s: -1)
        self._extract_sleep_recommendation = get_sleep_time or (lambda _e: 0.0)
        self._on_invoke = lambda _v: None

    def on_invoke(self, fn: LLMInvocationFn | None) -> None:
        """
        设置调用完成后的回调函数

        Args:
            fn: 调用完成回调函数,接收调用结果作为参数
        """
        self._on_invoke = fn or (lambda _v: None)

    def count_request_tokens(self, input: TIn) -> int:
        """
        计算请求输入的 token 数量

        Args:
            input: 输入数据,可以是字符串,字符串列表或字典列表

        Returns
        -------
            token 数量,如果无法计算则返回 -1

        Raises
        ------
            TypeError: 如果输入类型不支持 token 计数
        """
        if isinstance(input, str):
            return self._count_tokens(input)
        if isinstance(input, list):
            result = 0
            for item in input:
                if isinstance(item, str):
                    result += self._count_tokens(item)
                elif isinstance(item, dict):
                    result += self._count_tokens(item.get("content", ""))
                else:
                    raise TypeError(_CANNOT_MEASURE_INPUT_TOKENS_MSG)
            return result
        raise TypeError(_CANNOT_MEASURE_INPUT_TOKENS_MSG)

    def count_response_tokens(self, output: TOut | None) -> int:
        """
        计算响应输出的 token 数量

        Args:
            output: 输出数据,可以是字符串,字符串列表或嵌入向量列表

        Returns
        -------
            token 数量,如果无法计算则返回 0

        Raises
        ------
            TypeError: 如果输出类型不支持 token 计数
        """
        if output is None:
            return 0
        if isinstance(output, str):
            return self._count_tokens(output)
        if isinstance(output, list) and all(isinstance(x, str) for x in output):
            return sum(self._count_tokens(item) for item in output)
        if isinstance(output, list):
            # 嵌入响应,不计数
            return 0
        raise TypeError(_CANNOT_MEASURE_OUTPUT_TOKENS_MSG)

    async def __call__(
        self,
        input: TIn,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[TOut]:
        """
        执行带速率限制和重试机制的 LLM 调用

        主要流程:
        1. 检查任务状态
        2. 配置重试策略
        3. 等待速率限制器(如果有)
        4. 在信号量控制下执行 LLM 调用
        5. 处理速率限制错误和可重试错误
        6. 记录性能指标和 token 使用情况

        Args:
            input: 输入数据
            **kwargs: 额外的 LLM 输入参数

        Returns
        -------
            LLM 输出结果的包装对象

        Raises
        ------
            TaskStopError: 如果任务被取消或停止
            RetriesExhaustedError: 如果重试次数耗尽
        """
        # 检查任务是否停止
        self.check_task_stop()

        name = kwargs.get("name", "Process")
        attempt_number = 0
        call_times: list[float] = []
        input_tokens = self.count_request_tokens(input)
        max_retries = self._config.max_retries or 10
        max_retry_wait = self._config.max_retry_wait or 10
        follow_recommendation = self._config.sleep_on_rate_limit_recommendation

        # 配置重试策略:指数退避 + 抖动
        retryer = AsyncRetrying(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential_jitter(max=max_retry_wait),
            reraise=True,
            retry=retry_if_exception_type(tuple(self._retryable_errors)),
        )

        async def sleep_for(time: float | None) -> None:
            """
            处理速率限制错误的睡眠逻辑

            Args:
                time: 建议的睡眠时间(秒)

            Raises
            ------
                当前异常会被重新抛出以触发重试
            """
            log.warning(
                "%s failed to invoke LLM %s/%s attempts. Cause: rate limit exceeded, will retry. Recommended sleep for %d seconds. Follow recommendation? %s",
                name,
                attempt_number,
                max_retries,
                time,
                follow_recommendation,
            )
            if follow_recommendation and time:
                await asyncio.sleep(time)
            raise

        async def do_attempt() -> LLMOutput[TOut]:
            """
            执行单次 LLM 调用尝试

            Returns
            -------
                LLM 输出结果

            Raises
            ------
                BaseException: LLM 调用过程中的任何异常
            """
            self.check_task_stop("(1)")
            nonlocal call_times
            call_start = asyncio.get_event_loop().time()
            try:
                return await self._delegate(input, **kwargs)
            except BaseException as e:
                # 如果是速率限制错误,提取建议的睡眠时间
                if isinstance(e, tuple(self._rate_limit_errors)):
                    sleep_time = self._extract_sleep_recommendation(e)
                    await sleep_for(sleep_time)
                raise
            finally:
                call_end = asyncio.get_event_loop().time()
                call_times.append(call_end - call_start)

        async def execute_with_retry() -> tuple[LLMOutput[TOut], float]:
            """
            执行带重试机制的 LLM 调用

            Returns
            -------
                (LLM 输出结果, 开始时间) 的元组

            Raises
            ------
                RetriesExhaustedError: 如果重试次数耗尽
            """
            nonlocal attempt_number
            async for attempt in retryer:
                with attempt:
                    # 在调用前等待速率限制器(输入 token)
                    if self._rate_limiter and input_tokens > 0:
                        await self._rate_limiter.acquire(input_tokens)
                    start = asyncio.get_event_loop().time()
                    attempt_number += 1
                    return await do_attempt(), start

            log.error("Retries exhausted for %s", name)
            raise RetriesExhaustedError(name, max_retries)

        result: LLMOutput[TOut]
        start = 0.0

        # 根据是否有信号量选择执行方式
        if self._semaphore is None:
            result, start = await execute_with_retry()
        else:
            async with self._semaphore:
                result, start = await execute_with_retry()

        end = asyncio.get_event_loop().time()
        output_tokens = self.count_response_tokens(result.output)

        # 在调用后等待速率限制器(输出 token)
        if self._rate_limiter and output_tokens > 0:
            await self._rate_limiter.acquire(output_tokens)

        # 构建调用结果并触发回调
        invocation_result = LLMInvocationResult(
            result=result,
            name=name,
            num_retries=attempt_number - 1,
            total_time=end - start,
            call_times=call_times,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self._handle_invoke_result(invocation_result)
        return result

    def _handle_invoke_result(
        self, result: LLMInvocationResult[LLMOutput[TOut]]
    ) -> None:
        """
        处理 LLM 调用结果

        记录性能日志并更新任务的 token 使用统计。

        Args:
            result: LLM 调用结果对象
        """
        log.info(
            'perf - llm.%s "%s" with %s retries took %s. input_tokens=%d, output_tokens=%d',
            self._operation,
            result.name,
            result.num_retries,
            result.total_time,
            result.input_tokens,
            result.output_tokens,
        )
        self._on_invoke(result)

        # 记录调用次数和 token 使用情况到任务上下文
        task_factory = _get_task_factory()
        task = task_factory.get_task(threading.current_thread())
        if task:
            task.add_token_info(1, result.input_tokens, result.output_tokens)

    def check_task_stop(self, msg=""):
        """
        检查任务是否已停止或取消

        Args:
            msg: 额外的日志消息前缀

        Raises:
            TaskStopError: 如果任务已停止,取消或不存在
        """
        task_factory = _get_task_factory()
        TaskStopError = _get_task_stop_error()
        task = task_factory.get_task(threading.current_thread())
        if task:
            if task.is_cancelling():
                print(f"{msg}任务取消中: {task.taskId}-{task.status}")
                log.info(f"{msg}任务取消中: {task.taskId}-{task.status}")
                raise TaskStopError(f"{msg}任务取消中!!! {task.taskId}-{task.status}")

            if task.is_running() is False:
                print(f"{msg}任务已经停止: {task.taskId}-{task.status}")
                log.info(f"{msg}任务已经停止: {task.taskId}-{task.status}")
                raise TaskStopError(f"{msg}任务已经停止!!! {task.taskId}-{task.status}")
        else:
            print("{msg}任务不存在")
            log.info("{msg}任务不存在")
            raise TaskStopError(f"{msg}任务不存在!!!")
