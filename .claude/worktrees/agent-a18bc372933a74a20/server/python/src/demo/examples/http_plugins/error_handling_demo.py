"""
错误处理与重试示例

演示 HTTP 插件的错误处理：
- 请求超时处理
- 自动重试机制
- 异常捕获

示例使用：
    client = RetryableHTTPClient(max_retries=3)
    response = client.get("https://api.example.com")
"""

import time
from dataclasses import dataclass
from typing import Any
from collections.abc import Callable


@dataclass
class RetryConfig:
    """重试配置"""

    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    retry_on: tuple[type[Exception], ...] = (Exception,)


class RetryableHTTPClient:
    """支持重试的 HTTP 客户端"""

    def __init__(
        self,
        config: RetryConfig | None = None,
        request_func: Callable[..., Any] | None = None,
    ) -> None:
        """初始化客户端

        Args:
            config: 重试配置
            request_func: 自定义请求函数（用于测试）
        """
        self.config = config or RetryConfig()
        self._request_func = request_func
        self._attempt_count = 0

    def get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """发送 GET 请求（带重试）

        Args:
            url: 请求 URL
            **kwargs: 其他参数

        Returns:
            响应数据

        Raises:
            Exception: 重试次数用尽后抛出异常
        """
        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            self._attempt_count = attempt + 1
            try:
                return self._do_request(url, **kwargs)
            except self.config.retry_on as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (
                        self.config.backoff_factor**attempt
                    )
                    time.sleep(delay)
                    continue
                raise

        # 不应该到达这里，但类型检查需要
        if last_exception:
            raise last_exception
        raise RuntimeError("未知错误")

    def _do_request(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """执行实际请求"""
        if self._request_func:
            return self._request_func(url, **kwargs)

        # Mock 实现
        return {"status": "ok", "url": url}

    @property
    def attempt_count(self) -> int:
        """返回最近请求的尝试次数"""
        return self._attempt_count


class TimeoutHandler:
    """超时处理器"""

    def __init__(self, timeout: float = 5.0) -> None:
        """初始化

        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """执行函数，超时则抛出异常

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            TimeoutError: 执行超时
        """
        import signal

        def timeout_handler(signum: int, frame: Any) -> None:
            raise TimeoutError(f"执行超时 ({self.timeout}秒)")

        # 设置信号处理器（仅 Unix）
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, self.timeout)

        try:
            result = func(*args, **kwargs)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)

        return result


class ErrorHandler:
    """错误处理器"""

    @staticmethod
    def handle_timeout(error: TimeoutError) -> dict[str, Any]:
        """处理超时错误"""
        return {
            "error": "timeout",
            "message": "请求超时，请稍后重试",
        }

    @staticmethod
    def handle_network_error(error: Exception) -> dict[str, Any]:
        """处理网络错误"""
        return {
            "error": "network",
            "message": f"网络错误: {str(error)}",
        }

    @staticmethod
    def handle_unknown_error(error: Exception) -> dict[str, Any]:
        """处理未知错误"""
        return {
            "error": "unknown",
            "message": f"未知错误: {str(error)}",
        }

    def handle(self, error: Exception) -> dict[str, Any]:
        """统一错误处理

        Args:
            error: 异常实例

        Returns:
            错误信息字典
        """
        if isinstance(error, TimeoutError):
            return self.handle_timeout(error)
        if isinstance(error, (ConnectionError, OSError)):
            return self.handle_network_error(error)
        return self.handle_unknown_error(error)


def error_handling_demo() -> None:
    """演示错误处理功能"""
    print("=" * 50)
    print("错误处理与重试示例")
    print("=" * 50)

    # 重试演示
    print("\n1. 重试机制演示")

    call_count = 0

    def flaky_request(url: str, **kwargs: Any) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("模拟网络错误")
        return {"status": "ok", "attempts": call_count}

    config = RetryConfig(max_retries=3, retry_delay=0.1)
    client = RetryableHTTPClient(config=config, request_func=flaky_request)

    result = client.get("https://api.example.com")
    print(f"   请求成功，尝试次数: {client.attempt_count}")
    print(f"   结果: {result}")

    # 错误处理演示
    print("\n2. 错误处理演示")
    handler = ErrorHandler()

    errors = [
        TimeoutError("连接超时"),
        ConnectionError("网络不可达"),
        ValueError("未知错误"),
    ]

    for error in errors:
        result = handler.handle(error)
        print(f"   {type(error).__name__}: {result['message']}")


def demo() -> None:
    """演示入口"""
    error_handling_demo()


if __name__ == "__main__":
    demo()
