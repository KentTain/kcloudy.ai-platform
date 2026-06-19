"""
PropertyUtil 工具类单元测试
"""

from datetime import datetime
from decimal import Decimal

import pytest

from framework.database import AttributeDataType
from framework.utils.property_util import PropertyUtil


class MockAttribute:
    """模拟属性对象"""

    def __init__(self, name: str, value: str, data_type: str = "string"):
        self.name = name
        self.value = value
        self.data_type = data_type


class TestCoerceValue:
    """coerce_value 类型转换测试"""

    def test_coerce_string(self):
        """字符串类型应原样返回"""
        result = PropertyUtil.coerce_value("hello", AttributeDataType.STRING)
        assert result == "hello"

    def test_coerce_integer(self):
        """整数类型转换"""
        result = PropertyUtil.coerce_value("587", AttributeDataType.INTEGER)
        assert result == 587
        assert isinstance(result, int)

    def test_coerce_integer_negative(self):
        """负整数转换"""
        result = PropertyUtil.coerce_value("-42", AttributeDataType.INTEGER)
        assert result == -42

    def test_coerce_integer_invalid_raises(self):
        """无效整数应抛出 ValueError"""
        with pytest.raises(ValueError):
            PropertyUtil.coerce_value("abc", AttributeDataType.INTEGER)

    def test_coerce_decimal(self):
        """小数类型转换"""
        result = PropertyUtil.coerce_value("3.14", AttributeDataType.DECIMAL)
        assert result == Decimal("3.14")
        assert isinstance(result, Decimal)

    def test_coerce_decimal_negative(self):
        """负小数转换"""
        result = PropertyUtil.coerce_value("-2.5", AttributeDataType.DECIMAL)
        assert result == Decimal("-2.5")

    def test_coerce_decimal_invalid_raises(self):
        """无效小数应抛出 ValueError"""
        with pytest.raises(ValueError):
            PropertyUtil.coerce_value("not_a_number", AttributeDataType.DECIMAL)

    def test_coerce_boolean_true(self):
        """布尔值 true 转换"""
        for val in ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]:
            result = PropertyUtil.coerce_value(val, AttributeDataType.BOOLEAN)
            assert result is True

    def test_coerce_boolean_false(self):
        """布尔值 false 转换"""
        for val in ["false", "FALSE", "False", "0", "no", "NO", "off", "OFF"]:
            result = PropertyUtil.coerce_value(val, AttributeDataType.BOOLEAN)
            assert result is False

    def test_coerce_boolean_invalid_raises(self):
        """无效布尔值应抛出 ValueError"""
        with pytest.raises(ValueError):
            PropertyUtil.coerce_value("maybe", AttributeDataType.BOOLEAN)

    def test_coerce_date_time_iso(self):
        """ISO 格式日期时间转换"""
        result = PropertyUtil.coerce_value("2026-05-24T10:00:00", AttributeDataType.DATE_TIME)
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 24

    def test_coerce_date_time_iso_with_z(self):
        """带 Z 的 ISO 格式日期时间转换"""
        result = PropertyUtil.coerce_value("2026-05-24T10:00:00Z", AttributeDataType.DATE_TIME)
        assert isinstance(result, datetime)
        assert result.year == 2026

    def test_coerce_date_time_custom_format(self):
        """自定义格式日期时间转换"""
        result = PropertyUtil.coerce_value("2026-05-24 10:30:00", AttributeDataType.DATE_TIME)
        assert isinstance(result, datetime)
        assert result.hour == 10
        assert result.minute == 30

    def test_coerce_date_time_date_only(self):
        """仅日期格式转换"""
        result = PropertyUtil.coerce_value("2026-05-24", AttributeDataType.DATE_TIME)
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 24

    def test_coerce_date_time_invalid_raises(self):
        """无效日期时间应抛出 ValueError"""
        with pytest.raises(ValueError):
            PropertyUtil.coerce_value("not_a_date", AttributeDataType.DATE_TIME)

    def test_coerce_json(self):
        """JSON 类型转换"""
        result = PropertyUtil.coerce_value('{"key": "value", "number": 42}', AttributeDataType.JSON)
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_coerce_json_array(self):
        """JSON 数组转换"""
        result = PropertyUtil.coerce_value("[1, 2, 3]", AttributeDataType.JSON)
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_coerce_json_invalid_raises(self):
        """无效 JSON 应抛出 ValueError"""
        with pytest.raises(ValueError):
            PropertyUtil.coerce_value("{invalid_json}", AttributeDataType.JSON)

    def test_coerce_none_value(self):
        """None 值应返回 None"""
        result = PropertyUtil.coerce_value(None, AttributeDataType.STRING)
        assert result is None


class TestGetAttributeByName:
    """get_attribute_by_name 测试"""

    def test_get_attribute_found(self):
        """找到属性"""
        attrs = [
            MockAttribute("host", "localhost"),
            MockAttribute("port", "5432"),
        ]
        result = PropertyUtil.get_attribute_by_name(attrs, "port")
        assert result is not None
        assert result.value == "5432"

    def test_get_attribute_not_found(self):
        """未找到属性返回 None"""
        attrs = [
            MockAttribute("host", "localhost"),
        ]
        result = PropertyUtil.get_attribute_by_name(attrs, "nonexistent")
        assert result is None

    def test_get_attribute_empty_list(self):
        """空列表返回 None"""
        result = PropertyUtil.get_attribute_by_name([], "any")
        assert result is None


class TestGetValueByName:
    """get_value_by_name 测试"""

    def test_get_value_found(self):
        """找到属性值"""
        attrs = [
            MockAttribute("host", "localhost"),
        ]
        result = PropertyUtil.get_value_by_name(attrs, "host")
        assert result == "localhost"

    def test_get_value_not_found_default(self):
        """未找到返回默认值"""
        attrs = []
        result = PropertyUtil.get_value_by_name(attrs, "host", default="default_host")
        assert result == "default_host"

    def test_get_value_default_empty_string(self):
        """默认默认值为空字符串"""
        attrs = []
        result = PropertyUtil.get_value_by_name(attrs, "any")
        assert result == ""


class TestGetValuesByName:
    """get_values_by_name 测试"""

    def test_get_values_single(self):
        """单个匹配"""
        attrs = [
            MockAttribute("tag", "production"),
        ]
        result = PropertyUtil.get_values_by_name(attrs, "tag")
        assert result == ["production"]

    def test_get_values_multiple(self):
        """多个匹配"""
        attrs = [
            MockAttribute("tag", "production"),
            MockAttribute("tag", "api"),
            MockAttribute("tag", "v2"),
        ]
        result = PropertyUtil.get_values_by_name(attrs, "tag")
        assert result == ["production", "api", "v2"]

    def test_get_values_not_found(self):
        """未找到返回空列表"""
        attrs = [
            MockAttribute("name", "test"),
        ]
        result = PropertyUtil.get_values_by_name(attrs, "tag")
        assert result == []


class TestGetTypedValue:
    """get_typed_value 测试"""

    def test_get_typed_value_with_data_type(self):
        """使用 data_type 转换"""
        attrs = [
            MockAttribute("port", "5432", "integer"),
        ]
        result = PropertyUtil.get_typed_value(attrs, "port", int)
        assert result == 5432
        assert isinstance(result, int)

    def test_get_typed_value_not_found(self):
        """未找到返回默认值"""
        attrs = []
        result = PropertyUtil.get_typed_value(attrs, "any", int, default=100)
        assert result == 100

    def test_get_typed_value_none_value(self):
        """值为 None 返回默认值"""
        attrs = [
            MockAttribute("value", None, "string"),
        ]
        result = PropertyUtil.get_typed_value(attrs, "value", str, default="default")
        assert result == "default"
