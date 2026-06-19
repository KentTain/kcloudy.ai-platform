"""
自定义工具示例单元测试

测试 custom_tools 模块的所有示例代码。
"""

import pytest

from demo.examples.custom_tools.basic_tool_demo import (
    CalculatorTool,
    calculate,
    create_weather_tool,
    get_current_time,
    search_web,
    translate_text,
)
from demo.examples.custom_tools.structured_tool_demo import (
    DatabaseQueryInput,
    DatabaseQueryTool,
    EmailInput,
    EmailTool,
    SearchInput,
    SearchTool,
)
from demo.examples.custom_tools.tool_chain_demo import (
    ConditionalToolChain,
    SimpleToolChain,
    calculate_discount,
    calculate_price,
    fetch_user_info,
)


class TestBasicTools:
    """测试基础工具"""

    def test_get_current_time(self) -> None:
        """测试时间工具"""
        result = get_current_time.invoke({"timezone": "Asia/Shanghai"})
        assert isinstance(result, str)
        assert len(result) > 0
        # 应该包含日期格式
        assert "-" in result  # 日期分隔符
        assert ":" in result  # 时间分隔符

    def test_get_current_time_invalid_timezone(self) -> None:
        """测试无效时区"""
        result = get_current_time.invoke({"timezone": "Invalid/Timezone"})
        assert "未知时区" in result

    def test_calculate_simple(self) -> None:
        """测试简单计算"""
        result = calculate.invoke({"expression": "2 + 3"})
        assert result == "5"

    def test_calculate_complex(self) -> None:
        """测试复杂计算"""
        result = calculate.invoke({"expression": "2 + 3 * 4"})
        assert result == "14"

    def test_calculate_with_parentheses(self) -> None:
        """测试带括号的计算"""
        result = calculate.invoke({"expression": "(2 + 3) * 4"})
        assert result == "20"

    def test_calculate_invalid_expression(self) -> None:
        """测试无效表达式"""
        result = calculate.invoke({"expression": "abc"})
        assert "计算错误" in result

    def test_search_web(self) -> None:
        """测试搜索工具"""
        result = search_web.invoke({"query": "Python", "max_results": 3})
        assert "Python" in result
        assert "3 个结果" in result

    def test_translate_text(self) -> None:
        """测试翻译工具"""
        result = translate_text.invoke(
            {"text": "你好", "source_lang": "zh", "target_lang": "en"}
        )
        assert "[zh -> en]" in result
        assert "你好" in result


class TestCalculatorToolClass:
    """测试计算器工具类"""

    def test_add(self) -> None:
        """测试加法"""
        result = CalculatorTool.add.invoke({"a": 2, "b": 3})
        assert result == 5

    def test_subtract(self) -> None:
        """测试减法"""
        result = CalculatorTool.subtract.invoke({"a": 5, "b": 3})
        assert result == 2

    def test_multiply(self) -> None:
        """测试乘法"""
        result = CalculatorTool.multiply.invoke({"a": 4, "b": 3})
        assert result == 12

    def test_divide(self) -> None:
        """测试除法"""
        result = CalculatorTool.divide.invoke({"a": 10, "b": 2})
        assert result == "5.0"

    def test_divide_by_zero(self) -> None:
        """测试除以零"""
        result = CalculatorTool.divide.invoke({"a": 10, "b": 0})
        assert "除数不能为零" in result

    def test_get_tools(self) -> None:
        """测试获取所有工具"""
        tools = CalculatorTool.get_tools()
        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "add" in tool_names
        assert "subtract" in tool_names
        assert "multiply" in tool_names
        assert "divide" in tool_names


class TestWeatherTool:
    """测试天气工具"""

    def test_create_weather_tool(self) -> None:
        """测试创建天气工具"""
        weather_tool = create_weather_tool()
        assert weather_tool.name == "get_weather"

    def test_get_weather_known_city(self) -> None:
        """测试已知城市天气"""
        weather_tool = create_weather_tool()
        result = weather_tool.invoke({"city": "北京"})
        # 检查返回结果不为空且包含温度信息
        assert len(result) > 0
        assert "°C" in result or "25" in result

    def test_get_weather_unknown_city(self) -> None:
        """测试未知城市天气"""
        weather_tool = create_weather_tool()
        result = weather_tool.invoke({"city": "火星城"})
        assert "未找到" in result or "火星城" in result


class TestStructuredTools:
    """测试结构化工具"""

    def test_search_input_validation(self) -> None:
        """测试搜索输入验证"""
        # 有效输入
        input_data = SearchInput(query="test", max_results=5)
        assert input_data.query == "test"
        assert input_data.max_results == 5

    def test_search_input_max_results_bounds(self) -> None:
        """测试搜索结果数边界"""
        # 最小值
        input_data = SearchInput(query="test", max_results=1)
        assert input_data.max_results == 1

        # 超过最大值应该抛出异常
        with pytest.raises(Exception, match=".*"):
            SearchInput(query="test", max_results=100)

    def test_search_tool(self) -> None:
        """测试搜索工具"""
        tool = SearchTool().create_tool()
        result = tool.invoke(
            {"query": "LangChain", "max_results": 2, "include_images": False}
        )
        assert "LangChain" in result
        assert "2 个结果" in result

    def test_database_query_tool(self) -> None:
        """测试数据库查询工具"""
        tool = DatabaseQueryTool().create_tool()

        # 查询用户表
        result = tool.invoke({"table_name": "users", "columns": ["name"], "limit": 2})
        assert "张三" in result or "李四" in result

    def test_database_query_invalid_table(self) -> None:
        """测试查询无效表"""
        tool = DatabaseQueryTool().create_tool()
        result = tool.invoke({"table_name": "invalid_table"})
        assert "不存在" in result

    def test_email_tool(self) -> None:
        """测试邮件工具"""
        tool = EmailTool.create_tool()
        result = tool.invoke(
            {
                "to": "user@example.com",
                "subject": "Test",
                "body": "Hello",
                "priority": "high",
            }
        )
        assert "发送成功" in result
        assert "user@example.com" in result

    def test_email_tool_invalid_email(self) -> None:
        """测试无效邮箱"""
        tool = EmailTool.create_tool()
        result = tool.invoke(
            {"to": "invalid-email", "subject": "Test", "body": "Hello"}
        )
        assert "无效" in result or "错误" in result


class TestToolChain:
    """测试工具链"""

    def test_simple_tool_chain(self) -> None:
        """测试简单工具链"""
        chain = SimpleToolChain(
            [
                fetch_user_info,
                calculate_discount,
            ]
        )

        result = chain.run({"user_id": "001"})
        assert result["success"] is True
        assert "final_result" in result

    def test_tool_chain_with_price(self) -> None:
        """测试带价格计算的工具链"""
        chain = SimpleToolChain(
            [
                fetch_user_info,
                calculate_discount,
                calculate_price,
            ]
        )

        result = chain.run({"user_id": "001", "base_price": 1000})
        assert result["success"] is True
        final = result["final_result"]
        assert "final_price" in final
        # gold 会员 8 折，验证有折扣
        assert final["final_price"] < 1000

    def test_tool_chain_invalid_user(self) -> None:
        """测试无效用户的工具链"""
        chain = SimpleToolChain(
            [
                fetch_user_info,
                calculate_discount,
            ]
        )

        result = chain.run({"user_id": "999"})
        assert "error" in result or "final_result" in result

    def test_conditional_tool_chain(self) -> None:
        """测试条件工具链"""
        chain = ConditionalToolChain()

        # Gold 会员应该有通知
        result = chain.run_order_flow("001", 100)
        assert "notification" in result
        assert "price_info" in result

        # Silver 会员没有通知
        result = chain.run_order_flow("002", 100)
        assert "notification" not in result
        assert "price_info" in result


class TestToolInputSchemas:
    """测试工具输入模型"""

    def test_search_input_schema(self) -> None:
        """测试搜索输入模型"""
        schema = SearchInput.model_json_schema()
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]
        assert "include_images" in schema["properties"]

    def test_database_query_input_schema(self) -> None:
        """测试数据库查询输入模型"""
        schema = DatabaseQueryInput.model_json_schema()
        assert "table_name" in schema["properties"]
        assert "columns" in schema["properties"]
        assert "where_clause" in schema["properties"]
        assert "limit" in schema["properties"]

    def test_email_input_schema(self) -> None:
        """测试邮件输入模型"""
        schema = EmailInput.model_json_schema()
        assert "to" in schema["properties"]
        assert "subject" in schema["properties"]
        assert "body" in schema["properties"]
        assert "cc" in schema["properties"]
        assert "priority" in schema["properties"]
