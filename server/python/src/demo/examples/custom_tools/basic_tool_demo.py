"""
@tool 装饰器基础工具示例

演示如何使用 @tool 装饰器快速创建 LangChain 工具。
这是最简单的工具创建方式，适合单一功能的工具。

Day 3 讲义：AI 智能体应用实战 - 自定义工具开发
"""

from typing import Annotated

from langchain_core.tools import tool

# ==================== 简单函数工具 ====================


@tool
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """
    获取指定时区的当前时间

    Args:
        timezone: 时区名称，如 'Asia/Shanghai', 'America/New_York'

    Returns:
        当前时间的字符串表示
    """
    from datetime import datetime

    import pytz

    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except pytz.UnknownTimeZoneError:
        return f"未知时区: {timezone}"


@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 数学表达式，如 '2 + 3 * 4'

    Returns:
        计算结果
    """
    import ast
    import operator

    # 安全的表达式求值
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def eval_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_func = operators.get(type(node.op))
            if op_func:
                return op_func(left, right)
            raise ValueError(f"不支持的操作符: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op_func = operators.get(type(node.op))
            if op_func:
                return op_func(operand)
            raise ValueError(f"不支持的操作符: {type(node.op)}")
        else:
            raise ValueError(f"不支持的表达式类型: {type(node)}")

    try:
        tree = ast.parse(expression, mode="eval")
        result = eval_node(tree.body)
        return str(result)
    except Exception as e:
        return f"计算错误: {e!s}"


# ==================== 带类型注解的工具 ====================


@tool
def search_web(
    query: Annotated[str, "搜索关键词"],
    max_results: Annotated[int, "最大返回结果数，默认5"] = 5,
) -> str:
    """
    在网络上搜索信息（模拟）

    这是一个模拟的搜索工具，实际应用中需要接入真实的搜索 API。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数

    Returns:
        搜索结果字符串
    """
    # 模拟搜索结果
    mock_results = [
        {"title": f"关于 {query} 的介绍", "url": f"https://example.com/{query}/intro"},
        {
            "title": f"{query} 最佳实践",
            "url": f"https://example.com/{query}/best-practices",
        },
        {"title": f"{query} 教程", "url": f"https://example.com/{query}/tutorial"},
    ]

    results = mock_results[:max_results]
    output = f"搜索 '{query}' 找到 {len(results)} 个结果：\n"
    for i, r in enumerate(results, 1):
        output += f"{i}. {r['title']} - {r['url']}\n"

    return output


@tool
def translate_text(
    text: str,
    source_lang: Annotated[str, "源语言代码，如 'zh', 'en'"] = "auto",
    target_lang: Annotated[str, "目标语言代码，如 'zh', 'en'"] = "en",
) -> str:
    """
    翻译文本（模拟）

    这是一个模拟的翻译工具。

    Args:
        text: 要翻译的文本
        source_lang: 源语言代码
        target_lang: 目标语言代码

    Returns:
        翻译结果
    """
    # 模拟翻译
    return f"[{source_lang} -> {target_lang}] {text} (翻译结果)"


# ==================== 工具类封装 ====================


class CalculatorTool:
    """
    计算器工具类

    展示如何将多个相关工具组织在一起。
    """

    @staticmethod
    @tool
    def add(a: float, b: float) -> float:
        """加法运算：a + b"""
        return a + b

    @staticmethod
    @tool
    def subtract(a: float, b: float) -> float:
        """减法运算：a - b"""
        return a - b

    @staticmethod
    @tool
    def multiply(a: float, b: float) -> float:
        """乘法运算：a * b"""
        return a * b

    @staticmethod
    @tool
    def divide(a: float, b: float) -> str:
        """除法运算：a / b"""
        if b == 0:
            return "错误：除数不能为零"
        return str(a / b)

    @classmethod
    def get_tools(cls) -> list:
        """获取所有工具"""
        return [
            cls.add,
            cls.subtract,
            cls.multiply,
            cls.divide,
        ]


# ==================== 天气工具工厂 ====================


def create_weather_tool():
    """
    创建天气查询工具

    展示如何动态创建工具。
    """

    @tool
    def get_weather(city: str) -> str:
        """
        查询指定城市的天气（模拟）

        Args:
            city: 城市名称

        Returns:
            天气信息
        """
        # 模拟天气数据
        weather_data = {
            "北京": "晴天，气温 25°C，空气质量良好",
            "上海": "多云，气温 28°C，有轻微雾霾",
            "广州": "小雨，气温 30°C，湿度较高",
            "深圳": "晴转多云，气温 29°C",
        }

        return weather_data.get(city, f"未找到 {city} 的天气信息，请检查城市名称")

    return get_weather


# ==================== 演示函数 ====================


def demo_basic_tools() -> None:
    """演示基础工具的使用"""
    print("=== 基础工具演示 ===\n")

    # 时间工具
    print("1. 时间工具：")
    print(f"   北京时间: {get_current_time.invoke({'timezone': 'Asia/Shanghai'})}")
    print(f"   纽约时间: {get_current_time.invoke({'timezone': 'America/New_York'})}")
    print()

    # 计算器工具
    print("2. 计算器工具：")
    print(f"   2 + 3 * 4 = {calculate.invoke({'expression': '2 + 3 * 4'})}")
    print(f"   (10 + 5) / 3 = {calculate.invoke({'expression': '(10 + 5) / 3'})}")
    print()

    # 搜索工具
    print("3. 搜索工具：")
    print(search_web.invoke({"query": "Python", "max_results": 2}))
    print()

    # 翻译工具
    print("4. 翻译工具：")
    print(
        translate_text.invoke(
            {"text": "你好，世界！", "source_lang": "zh", "target_lang": "en"}
        )
    )
    print()

    # 计算器工具类
    print("5. 计算器工具类：")
    for tool_func in CalculatorTool.get_tools():
        print(f"   - {tool_func.name}: {tool_func.description}")


if __name__ == "__main__":
    demo_basic_tools()
