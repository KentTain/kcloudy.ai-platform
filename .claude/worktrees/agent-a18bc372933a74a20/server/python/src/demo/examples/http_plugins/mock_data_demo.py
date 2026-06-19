"""
Mock 数据示例

演示如何为 HTTP 插件提供 Mock 数据：
- 预设数据配置
- 动态数据生成
- 场景切换

示例使用：
    provider = MockDataProvider()
    data = provider.get_weather("北京")
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockDataConfig:
    """Mock 数据配置"""

    # 默认场景
    scenario: str = "normal"

    # 各场景数据
    scenarios: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "normal": {
                "北京": {"temperature": "25℃", "weather": "晴"},
                "上海": {"temperature": "28℃", "weather": "多云"},
            },
            "rainy": {
                "北京": {"temperature": "18℃", "weather": "雨"},
                "上海": {"temperature": "20℃", "weather": "暴雨"},
            },
            "hot": {
                "北京": {"temperature": "38℃", "weather": "高温"},
                "上海": {"temperature": "40℃", "weather": "酷热"},
            },
        }
    )


class MockDataProvider:
    """Mock 数据提供者

    根据配置提供 Mock 数据。
    """

    def __init__(self, config: MockDataConfig | None = None) -> None:
        """初始化

        Args:
            config: Mock 数据配置
        """
        self.config = config or MockDataConfig()

    def set_scenario(self, scenario: str) -> None:
        """切换场景

        Args:
            scenario: 场景名称
        """
        if scenario not in self.config.scenarios:
            raise ValueError(f"未知场景: {scenario}")
        self.config.scenario = scenario

    def get_weather(self, city: str) -> dict[str, Any]:
        """获取天气 Mock 数据

        Args:
            city: 城市名称

        Returns:
            天气数据
        """
        scenario_data = self.config.scenarios.get(self.config.scenario, {})
        default = {
            "temperature": "20℃",
            "weather": "未知",
            "scenario": self.config.scenario,
        }
        result = scenario_data.get(city, default).copy()
        result["city"] = city
        result["scenario"] = self.config.scenario
        return result

    def list_scenarios(self) -> list[str]:
        """列出所有场景"""
        return list(self.config.scenarios.keys())

    def list_cities(self) -> list[str]:
        """列出当前场景的城市"""
        scenario_data = self.config.scenarios.get(self.config.scenario, {})
        return list(scenario_data.keys())


class DynamicMockData:
    """动态 Mock 数据生成器"""

    def __init__(self) -> None:
        """初始化"""
        self._seed = 42

    def generate_temperature(self, city: str) -> str:
        """生成温度数据

        Args:
            city: 城市名称

        Returns:
            温度字符串
        """
        # 基于城市名生成伪随机温度
        base_temp = sum(ord(c) for c in city) % 20 + 15
        return f"{base_temp}℃"

    def generate_weather(self, city: str) -> str:
        """生成天气数据

        Args:
            city: 城市名称

        Returns:
            天气字符串
        """
        weathers = ["晴", "多云", "阴", "小雨", "大雨"]
        index = sum(ord(c) for c in city) % len(weathers)
        return weathers[index]

    def get_weather(self, city: str) -> dict[str, Any]:
        """获取动态生成的天气数据

        Args:
            city: 城市名称

        Returns:
            天气数据
        """
        return {
            "city": city,
            "temperature": self.generate_temperature(city),
            "weather": self.generate_weather(city),
        }


def mock_data_demo() -> None:
    """演示 Mock 数据功能"""
    print("=" * 50)
    print("Mock 数据示例")
    print("=" * 50)

    # 场景切换演示
    print("\n1. 场景切换演示")
    provider = MockDataProvider()

    print(f"可用场景: {provider.list_scenarios()}")
    print(f"当前场景: {provider.config.scenario}")

    # 不同场景的天气
    for scenario in ["normal", "rainy", "hot"]:
        provider.set_scenario(scenario)
        print(f"\n场景 '{scenario}':")
        for city in provider.list_cities():
            data = provider.get_weather(city)
            print(f"  {city}: {data['weather']}, {data['temperature']}")

    # 动态生成演示
    print("\n" + "-" * 50)
    print("\n2. 动态生成演示")
    dynamic = DynamicMockData()

    cities = ["北京", "上海", "广州", "深圳"]
    for city in cities:
        data = dynamic.get_weather(city)
        print(f"{city}: {data['weather']}, {data['temperature']}")


def demo() -> None:
    """演示入口"""
    mock_data_demo()


if __name__ == "__main__":
    demo()
