"""
内部 HTTP 客户端单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from framework.clients.inner_http_client import (
    InnerHttpClient,
    InnerServiceUnavailableError,
    InnerServiceTimeoutError,
)
from pydantic import BaseModel


class SampleResponse(BaseModel):
    """测试用响应模型"""
    id: str
    name: str


class TestInnerHttpClientInit:
    """初始化测试"""

    def test_init_with_defaults(self):
        """使用默认参数初始化"""
        client = InnerHttpClient()

        assert client.base_url is None
        assert client.timeout == 30.0
        assert client.service_name == "unknown"
        assert client.health_path == "/inner/v1/health"
        assert client._client is None

    def test_init_with_custom_params(self):
        """使用自定义参数初始化"""
        client = InnerHttpClient(
            base_url="http://localhost:8001",
            timeout=60.0,
            service_name="iam",
            health_path="/health",
        )

        assert client.base_url == "http://localhost:8001"
        assert client.timeout == 60.0
        assert client.service_name == "iam"
        assert client.health_path == "/health"


class TestInnerHttpClientGet:
    """GET 请求测试"""

    @pytest.mark.asyncio
    async def test_get_returns_dict_on_success(self):
        """成功请求返回字典"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "test"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.get("/api/users/1")

        assert result == {"id": "1", "name": "test"}

    @pytest.mark.asyncio
    async def test_get_returns_model_when_provided(self):
        """提供响应模型时返回模型实例"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "test"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.get("/api/users/1", response_model=SampleResponse)

        assert isinstance(result, SampleResponse)
        assert result.id == "1"
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_returns_none_on_404(self):
        """404 响应返回 None"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.get("/api/users/999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_raises_timeout_error(self):
        """超时时抛出 InnerServiceTimeoutError"""
        client = InnerHttpClient(service_name="test", timeout=30.0)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = httpx.TimeoutException("timeout")
            mock_get_client.return_value = mock_http_client

            with pytest.raises(InnerServiceTimeoutError) as exc:
                await client.get("/api/users/1")

            assert exc.value.service_name == "test"
            assert exc.value.timeout == 30.0

    @pytest.mark.asyncio
    async def test_get_raises_unavailable_error(self):
        """请求错误时抛出 InnerServiceUnavailableError"""
        client = InnerHttpClient(service_name="test")

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = httpx.RequestError("connection failed")
            mock_get_client.return_value = mock_http_client

            with pytest.raises(InnerServiceUnavailableError) as exc:
                await client.get("/api/users/1")

            assert exc.value.service_name == "test"


class TestInnerHttpClientPost:
    """POST 请求测试"""

    @pytest.mark.asyncio
    async def test_post_returns_dict_on_success(self):
        """成功请求返回字典"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "created"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.post("/api/users", json={"name": "test"})

        assert result == {"id": "1", "name": "created"}

    @pytest.mark.asyncio
    async def test_post_returns_model_when_provided(self):
        """提供响应模型时返回模型实例"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "created"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.post(
                "/api/users",
                json={"name": "test"},
                response_model=SampleResponse,
            )

        assert isinstance(result, SampleResponse)
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_post_raises_timeout_error(self):
        """超时时抛出 InnerServiceTimeoutError"""
        client = InnerHttpClient(service_name="test", timeout=30.0)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = httpx.TimeoutException("timeout")
            mock_get_client.return_value = mock_http_client

            with pytest.raises(InnerServiceTimeoutError) as exc:
                await client.post("/api/users", json={"name": "test"})

            assert exc.value.service_name == "test"

    @pytest.mark.asyncio
    async def test_post_raises_unavailable_error(self):
        """请求错误时抛出 InnerServiceUnavailableError"""
        client = InnerHttpClient(service_name="test")

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = httpx.RequestError("connection failed")
            mock_get_client.return_value = mock_http_client

            with pytest.raises(InnerServiceUnavailableError) as exc:
                await client.post("/api/users", json={"name": "test"})

            assert exc.value.service_name == "test"


class TestInnerHttpClientHandleResponse:
    """响应处理测试"""

    def test_extracts_data_from_unified_response(self):
        """从统一响应格式中提取 data 字段"""
        client = InnerHttpClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {"id": "1", "name": "test"},
        }

        result = client._handle_response(mock_response)

        assert result == {"id": "1", "name": "test"}

    def test_returns_raw_data_when_no_data_field(self):
        """无 data 字段时返回原始数据"""
        client = InnerHttpClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "test"}

        result = client._handle_response(mock_response)

        assert result == {"id": "1", "name": "test"}

    def test_converts_to_model(self):
        """转换为 Pydantic 模型"""
        client = InnerHttpClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "test"}

        result = client._handle_response(mock_response, SampleResponse)

        assert isinstance(result, SampleResponse)
        assert result.id == "1"
        assert result.name == "test"

    def test_returns_none_on_404(self):
        """404 返回 None"""
        client = InnerHttpClient()
        mock_response = MagicMock()
        mock_response.status_code = 404

        result = client._handle_response(mock_response)

        assert result is None

    def test_raises_on_error_status(self):
        """错误状态码抛出异常"""
        client = InnerHttpClient()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        with pytest.raises(httpx.HTTPStatusError):
            client._handle_response(mock_response)


class TestInnerHttpClientHealthCheck:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_returns_true_when_healthy(self):
        """服务健康时返回 True"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_status_not_healthy(self):
        """状态非 healthy 时返回 False"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "unhealthy"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_non_200_status(self):
        """非 200 状态码返回 False"""
        client = InnerHttpClient(service_name="test")

        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self):
        """异常时返回 False"""
        client = InnerHttpClient(service_name="test")

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = Exception("connection error")
            mock_get_client.return_value = mock_http_client

            result = await client.health_check()

        assert result is False


class TestInnerHttpClientClose:
    """关闭客户端测试"""

    @pytest.mark.asyncio
    async def test_close_existing_client(self):
        """关闭已存在的客户端"""
        client = InnerHttpClient()

        mock_http_client = AsyncMock()
        client._client = mock_http_client

        await client.close()

        mock_http_client.aclose.assert_awaited_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_when_no_client(self):
        """无客户端时安全执行"""
        client = InnerHttpClient()
        client._client = None

        await client.close()

        assert client._client is None


class TestInnerHttpClientGetClient:
    """获取客户端测试"""

    @pytest.mark.asyncio
    async def test_creates_client_on_first_call(self):
        """首次调用创建客户端"""
        client = InnerHttpClient(base_url="http://localhost:8001", timeout=60.0)

        result = await client._get_client()

        assert isinstance(result, httpx.AsyncClient)
        assert client._client is result

        await client.close()

    @pytest.mark.asyncio
    async def test_reuses_existing_client(self):
        """复用已存在的客户端"""
        client = InnerHttpClient(base_url="http://localhost:8001")

        first = await client._get_client()
        second = await client._get_client()

        assert first is second

        await client.close()
