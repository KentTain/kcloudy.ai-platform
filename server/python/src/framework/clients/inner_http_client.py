"""
内部 HTTP 客户端

用于模块间 HTTP 调用，支持单体和微服务模式切换。
"""

from typing import Any, TypeVar

import httpx
from loguru import logger
from pydantic import BaseModel

_logger = logger.bind(name=__name__)

T = TypeVar("T", bound=BaseModel)


class InnerServiceUnavailableError(Exception):
    """内部服务不可用异常"""

    def __init__(self, service_name: str, detail: str):
        self.service_name = service_name
        self.detail = detail
        super().__init__(f"服务 {service_name} 不可用: {detail}")


class InnerServiceTimeoutError(Exception):
    """内部服务超时异常"""

    def __init__(self, service_name: str, timeout: float):
        self.service_name = service_name
        self.timeout = timeout
        super().__init__(f"服务 {service_name} 超时 ({timeout}s)")


class InnerHttpClient:
    """
    内部 HTTP 客户端

    用于模块间 HTTP 调用，支持单体和微服务模式切换。
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        service_name: str = "unknown",
        health_path: str = "/inner/v1/health",
    ):
        """
        初始化客户端

        Args:
            base_url: 基础 URL（微服务模式）
            timeout: 超时时间（秒）
            service_name: 服务名称（用于日志和错误信息）
            health_path: 健康检查路径
        """
        self.base_url = base_url
        self.timeout = timeout
        self.service_name = service_name
        self.health_path = health_path
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        path: str,
        response_model: type[T] | None = None,
    ) -> T | dict[str, Any] | None:
        """
        GET 请求

        Args:
            path: 请求路径
            response_model: 响应模型

        Returns:
            响应数据

        Raises:
            InnerServiceUnavailableError: 服务不可用
            InnerServiceTimeoutError: 请求超时
        """
        try:
            client = await self._get_client()
            response = await client.get(path)
            return self._handle_response(response, response_model)
        except httpx.TimeoutException:
            raise InnerServiceTimeoutError(self.service_name, self.timeout)
        except httpx.RequestError as e:
            raise InnerServiceUnavailableError(self.service_name, str(e))

    async def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> T | dict[str, Any] | None:
        """
        POST 请求

        Args:
            path: 请求路径
            json: 请求体
            response_model: 响应模型

        Returns:
            响应数据

        Raises:
            InnerServiceUnavailableError: 服务不可用
            InnerServiceTimeoutError: 请求超时
        """
        try:
            client = await self._get_client()
            response = await client.post(path, json=json)
            return self._handle_response(response, response_model)
        except httpx.TimeoutException:
            raise InnerServiceTimeoutError(self.service_name, self.timeout)
        except httpx.RequestError as e:
            raise InnerServiceUnavailableError(self.service_name, str(e))

    def _handle_response(
        self,
        response: httpx.Response,
        response_model: type[T] | None = None,
    ) -> T | dict[str, Any] | None:
        """处理响应"""
        if response.status_code == 404:
            return None

        response.raise_for_status()

        data = response.json()

        # 处理统一响应格式
        if isinstance(data, dict) and "data" in data:
            data = data["data"]

        if response_model and data is not None:
            return response_model.model_validate(data)

        return data

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否可用
        """
        try:
            client = await self._get_client()
            response = await client.get(self.health_path)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except Exception as e:
            _logger.warning(f"健康检查失败: {e}")
            return False
