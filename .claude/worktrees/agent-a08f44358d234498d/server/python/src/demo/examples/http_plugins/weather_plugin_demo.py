"""
天气查询插件示例

演示 HTTP 插件开发：
- 使用 @tool 装饰器注册工具
- 接收城市参数返回天气信息
- Mock 数据支持

示例使用：
    plugin = WeatherPlugin()
    result = plugin.get_weather("北京")
"""

from typing import Any

from langchain_core.tools import tool


class HTTPClient:
    """HTTP 客户端基类"""

    def get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """发送 GET 请求

        Args:
            url: 请求 URL
            **kwargs: 其他参数

        Returns:
            响应数据
        """
        raise NotImplementedError


class MockWeatherClient(HTTPClient):
    """Mock 天气客户端

    提供 Mock 数据，无需依赖真实 API。
    """

    # 预设的城市天气数据
    MOCK_DATA: dict[str, dict[str, Any]] = {
        "北京": {
            "temperature": "25℃",
            "weather": "晴",
            "humidity": "45%",
            "wind": "北风3级",
        },
        "上海": {
            "temperature": "28℃",
            "weather": "多云",
            "humidity": "65%",
            "wind": "东南风2级",
        },
        "广州": {
            "temperature": "32℃",
            "weather": "阵雨",
            "humidity": "80%",
            "wind": "南风2级",
        },
        "深圳": {
            "temperature": "31℃",
            "weather": "多云",
            "humidity": "75%",
            "wind": "东南风3级",
        },
    }

    def get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """返回 Mock 数据

        Args:
            url: 请求 URL（忽略）
            **kwargs: 其他参数

        Returns:
            Mock 天气数据
        """
        # 从 kwargs 或 params 中获取城市
        city = kwargs.get("params", {}).get("city", "北京")
        return self.MOCK_DATA.get(city, self._default_response(city))

    def _default_response(self, city: str) -> dict[str, Any]:
        """返回默认响应"""
        return {
            "temperature": "20℃",
            "weather": "未知",
            "humidity": "50%",
            "wind": "微风",
            "message": f"未找到城市 '{city}' 的天气数据",
        }


class WeatherPlugin:
    """天气查询插件

    使用 LangChain @tool 装饰器注册为工具。
    """

    def __init__(
        self,
        client: HTTPClient | None = None,
        use_mock: bool = True,
    ) -> None:
        """初始化天气插件

        Args:
            client: HTTP 客户端
            use_mock: 是否使用 Mock 数据
        """
        self.client = client or MockWeatherClient()
        self._use_mock = use_mock

    @property
    def use_mock(self) -> bool:
        """是否使用 Mock 模式"""
        return self._use_mock

    def get_weather(self, city: str) -> dict[str, Any]:
        """获取城市天气

        Args:
            city: 城市名称

        Returns:
            天气信息字典
        """
        if self._use_mock:
            return self._get_mock_weather(city)
        return self._get_real_weather(city)

    def _get_mock_weather(self, city: str) -> dict[str, Any]:
        """获取 Mock 天气数据"""
        assert isinstance(self.client, MockWeatherClient)
        return self.client.get("", params={"city": city})

    def _get_real_weather(self, city: str) -> dict[str, Any]:
        """获取真实天气数据（示例）"""
        # 实际实现中会调用真实 API
        url = f"https://api.weather.com/api?city={city}"
        return self.client.get(url)


def create_weather_tool() -> Any:
    """创建天气工具

    使用 @tool 装饰器创建 LangChain 工具。

    Returns:
        LangChain 工具
    """
    plugin = WeatherPlugin()

    @tool
    def weather_query(city: str) -> str:
        """查询城市天气。

        输入城市名称，返回该城市的天气信息。

        Args:
            city: 城市名称，如"北京"、"上海"

        Returns:
            天气信息字符串
        """
        result = plugin.get_weather(city)
        return f"{city}天气：{result['weather']}，温度{result['temperature']}，湿度{result['humidity']}，{result['wind']}"

    return weather_query


class WeatherPluginDemo:
    """天气插件演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.plugin = WeatherPlugin()

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("天气查询插件示例")
        print("=" * 50)

        cities = ["北京", "上海", "广州", "深圳", "未知城市"]

        print(f"\nMock 模式: {self.plugin.use_mock}")
        print("\n查询结果:")

        for city in cities:
            result = self.plugin.get_weather(city)
            print(f"\n{city}:")
            print(f"  天气: {result['weather']}")
            print(f"  温度: {result['temperature']}")
            print(f"  湿度: {result['humidity']}")
            print(f"  风力: {result['wind']}")
            if "message" in result:
                print(f"  提示: {result['message']}")

        # 演示 LangChain 工具
        print("\n" + "-" * 50)
        print("\nLangChain 工具集成:")
        tool = create_weather_tool()
        print(f"工具名称: {tool.name}")
        print(f"工具描述: {tool.description}")


def demo() -> None:
    """演示天气插件功能"""
    demo_instance = WeatherPluginDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
