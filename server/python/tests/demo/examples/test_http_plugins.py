"""
HTTP 插件示例单元测试

测试覆盖：
- 天气查询插件
- 错误处理与重试
- Mock 数据
"""

import pytest

from demo.examples.http_plugins.error_handling_demo import (
    ErrorHandler,
    RetryableHTTPClient,
    RetryConfig,
)
from demo.examples.http_plugins.mock_data_demo import (
    DynamicMockData,
    MockDataConfig,
    MockDataProvider,
)
from demo.examples.http_plugins.weather_plugin_demo import (
    HTTPClient,
    MockWeatherClient,
    WeatherPlugin,
    create_weather_tool,
)


class TestHTTPClient:
    """HTTPClient 基类测试"""

    def test_get_raises_not_implemented(self) -> None:
        """测试 get 方法抛出 NotImplementedError"""
        client = HTTPClient()
        with pytest.raises(NotImplementedError):
            client.get("https://example.com")


class TestMockWeatherClient:
    """MockWeatherClient 测试"""

    def test_get_beijing_weather(self) -> None:
        """测试获取北京天气"""
        client = MockWeatherClient()
        result = client.get("", params={"city": "北京"})
        assert result["temperature"] == "25℃"
        assert result["weather"] == "晴"

    def test_get_shanghai_weather(self) -> None:
        """测试获取上海天气"""
        client = MockWeatherClient()
        result = client.get("", params={"city": "上海"})
        assert result["temperature"] == "28℃"
        assert result["weather"] == "多云"

    def test_get_unknown_city(self) -> None:
        """测试未知城市返回默认数据"""
        client = MockWeatherClient()
        result = client.get("", params={"city": "未知城市"})
        assert result["weather"] == "未知"
        assert "message" in result


class TestWeatherPlugin:
    """WeatherPlugin 测试"""

    def test_init_default_mock_mode(self) -> None:
        """测试默认使用 Mock 模式"""
        plugin = WeatherPlugin()
        assert plugin.use_mock is True

    def test_get_weather_beijing(self) -> None:
        """测试获取北京天气"""
        plugin = WeatherPlugin()
        result = plugin.get_weather("北京")
        assert "temperature" in result
        assert "weather" in result

    def test_get_weather_returns_dict(self) -> None:
        """测试返回字典类型"""
        plugin = WeatherPlugin()
        result = plugin.get_weather("上海")
        assert isinstance(result, dict)


class TestCreateWeatherTool:
    """create_weather_tool 测试"""

    def test_tool_creation(self) -> None:
        """测试工具创建"""
        tool = create_weather_tool()
        assert tool.name == "weather_query"
        assert "查询城市天气" in tool.description


class TestRetryConfig:
    """RetryConfig 测试"""

    def test_default_values(self) -> None:
        """测试默认值"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.backoff_factor == 2.0

    def test_custom_values(self) -> None:
        """测试自定义值"""
        config = RetryConfig(max_retries=5, retry_delay=0.5)
        assert config.max_retries == 5
        assert config.retry_delay == 0.5


class TestRetryableHTTPClient:
    """RetryableHTTPClient 测试"""

    def test_success_on_first_try(self) -> None:
        """测试第一次请求成功"""

        def success_request(url: str, **kwargs: object) -> dict[str, str]:
            return {"status": "ok"}

        client = RetryableHTTPClient(request_func=success_request)
        result = client.get("https://example.com")
        assert result["status"] == "ok"
        assert client.attempt_count == 1

    def test_retry_on_failure(self) -> None:
        """测试失败后重试"""
        call_count = 0

        def flaky_request(url: str, **kwargs: object) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("失败")
            return {"status": "ok"}

        config = RetryConfig(max_retries=3, retry_delay=0.01)
        client = RetryableHTTPClient(config=config, request_func=flaky_request)
        result = client.get("https://example.com")
        assert result["status"] == "ok"
        assert client.attempt_count == 2

    def test_max_retries_exceeded(self) -> None:
        """测试超过最大重试次数"""

        def always_fail(url: str, **kwargs: object) -> None:
            raise ConnectionError("始终失败")

        config = RetryConfig(max_retries=2, retry_delay=0.01)
        client = RetryableHTTPClient(config=config, request_func=always_fail)
        with pytest.raises(ConnectionError):
            client.get("https://example.com")
        assert client.attempt_count == 3  # 初始 + 2 次重试


class TestErrorHandler:
    """ErrorHandler 测试"""

    def test_handle_timeout(self) -> None:
        """测试处理超时错误"""
        handler = ErrorHandler()
        result = handler.handle(TimeoutError("超时"))
        assert result["error"] == "timeout"
        assert "超时" in result["message"]

    def test_handle_network_error(self) -> None:
        """测试处理网络错误"""
        handler = ErrorHandler()
        result = handler.handle(ConnectionError("网络错误"))
        assert result["error"] == "network"

    def test_handle_unknown_error(self) -> None:
        """测试处理未知错误"""
        handler = ErrorHandler()
        result = handler.handle(ValueError("未知"))
        assert result["error"] == "unknown"


class TestMockDataConfig:
    """MockDataConfig 测试"""

    def test_default_scenario(self) -> None:
        """测试默认场景"""
        config = MockDataConfig()
        assert config.scenario == "normal"

    def test_scenarios_exist(self) -> None:
        """测试场景数据存在"""
        config = MockDataConfig()
        assert "normal" in config.scenarios
        assert "rainy" in config.scenarios


class TestMockDataProvider:
    """MockDataProvider 测试"""

    def test_get_weather(self) -> None:
        """测试获取天气"""
        provider = MockDataProvider()
        result = provider.get_weather("北京")
        assert "temperature" in result
        assert "weather" in result

    def test_set_scenario(self) -> None:
        """测试切换场景"""
        provider = MockDataProvider()
        provider.set_scenario("rainy")
        assert provider.config.scenario == "rainy"

    def test_set_invalid_scenario(self) -> None:
        """测试切换无效场景"""
        provider = MockDataProvider()
        with pytest.raises(ValueError, match="未知场景"):
            provider.set_scenario("invalid")

    def test_list_scenarios(self) -> None:
        """测试列出场景"""
        provider = MockDataProvider()
        scenarios = provider.list_scenarios()
        assert "normal" in scenarios
        assert "rainy" in scenarios


class TestDynamicMockData:
    """DynamicMockData 测试"""

    def test_generate_temperature(self) -> None:
        """测试生成温度"""
        data = DynamicMockData()
        temp = data.generate_temperature("北京")
        assert "℃" in temp

    def test_generate_weather(self) -> None:
        """测试生成天气"""
        data = DynamicMockData()
        weather = data.generate_weather("北京")
        assert weather in ["晴", "多云", "阴", "小雨", "大雨"]

    def test_deterministic(self) -> None:
        """测试确定性输出"""
        data = DynamicMockData()
        temp1 = data.generate_temperature("上海")
        temp2 = data.generate_temperature("上海")
        assert temp1 == temp2
