"""
utils 模块单元测试
"""

import pytest
from datetime import datetime, timedelta

from framework.utils.string_util import (
    to_snake_case,
    to_camel_case,
    mask_string,
    truncate_string,
    is_empty,
)
from framework.utils.time_util import (
    format_datetime,
    parse_datetime,
    timestamp_to_datetime,
    datetime_to_timestamp,
    humanize_time,
)
from framework.utils.enum_util import (
    get_enum_values,
    is_valid_enum_value,
    enum_to_dict,
)
from framework.utils.dictionary_util import (
    deep_merge,
    get_nested_value,
    set_nested_value,
    flatten_dict,
)
from framework.utils.json_util import json_dumps, json_loads


class TestStringUtils:
    """字符串工具测试"""

    def test_to_snake_case(self):
        """
        场景：驼峰转下划线
        WHEN: 输入 "UserName"
        THEN: 返回 "user_name"
        """
        assert to_snake_case("UserName") == "user_name"
        assert to_snake_case("XMLParser") == "xml_parser"
        assert to_snake_case("SimpleTest") == "simple_test"

    def test_to_camel_case(self):
        """
        场景：下划线转驼峰
        WHEN: 输入 "user_name"
        THEN: 返回 "userName"
        """
        assert to_camel_case("user_name") == "userName"
        assert to_camel_case("user_name", capitalize_first=True) == "UserName"

    def test_mask_string(self):
        """
        场景：字符串掩码
        WHEN: 输入手机号
        THEN: 返回掩码后的字符串
        """
        result = mask_string("13812345678", start=3, end=4)
        assert result == "138****5678"

    def test_mask_string_short(self):
        """
        场景：字符串过短
        WHEN: 字符串长度不足
        THEN: 返回原字符串
        """
        result = mask_string("abc", start=2, end=2)
        assert result == "abc"

    def test_truncate_string(self):
        """
        场景：截断字符串
        WHEN: 字符串超长
        THEN: 返回截断后的字符串
        """
        result = truncate_string("这是一个很长的字符串", max_length=8)
        assert len(result) <= 8

    def test_is_empty(self):
        """
        场景：空值检查
        WHEN: 检查各种空值
        THEN: 返回正确结果
        """
        assert is_empty(None) is True
        assert is_empty("") is True
        assert is_empty("   ") is True
        assert is_empty("test") is False


class TestTimeUtil:
    """时间工具测试"""

    def test_format_datetime(self):
        """
        场景：格式化日期时间
        WHEN: 输入 datetime
        THEN: 返回格式化字符串
        """
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_datetime(dt)
        assert result == "2024-01-15 10:30:45"

    def test_parse_datetime(self):
        """
        场景：解析日期时间
        WHEN: 输入字符串
        THEN: 返回 datetime
        """
        result = parse_datetime("2024-01-15 10:30:45")
        assert result == datetime(2024, 1, 15, 10, 30, 45)

    def test_parse_datetime_invalid(self):
        """
        场景：无效格式
        WHEN: 输入无效格式
        THEN: 返回 None
        """
        result = parse_datetime("invalid")
        assert result is None

    def test_timestamp_to_datetime(self):
        """
        场景：时间戳转 datetime
        WHEN: 输入时间戳
        THEN: 返回 datetime
        """
        # 2024-01-01 00:00:00 UTC
        ts = 1704067200
        result = timestamp_to_datetime(ts)
        assert isinstance(result, datetime)

    def test_humanize_time_just_now(self):
        """
        场景：刚刚
        WHEN: 时间差小于 60 秒
        THEN: 返回 "刚刚"
        """
        now = datetime.now()
        result = humanize_time(now, now=now)
        assert result == "刚刚"

    def test_humanize_time_minutes_ago(self):
        """
        场景：几分钟前
        WHEN: 时间差为分钟
        THEN: 返回 "X 分钟前"
        """
        now = datetime.now()
        past = now - timedelta(minutes=5)
        result = humanize_time(past, now=now)
        assert result == "5 分钟前"

    def test_humanize_time_hours_ago(self):
        """
        场景：几小时前
        WHEN: 时间差为小时
        THEN: 返回 "X 小时前"
        """
        now = datetime.now()
        past = now - timedelta(hours=3)
        result = humanize_time(past, now=now)
        assert result == "3 小时前"

    def test_humanize_time_days_ago(self):
        """
        场景：几天前
        WHEN: 时间差为天
        THEN: 返回 "X 天前"
        """
        now = datetime.now()
        past = now - timedelta(days=5)
        result = humanize_time(past, now=now)
        assert result == "5 天前"


class TestEnumUtil:
    """枚举工具测试"""

    def test_get_enum_values(self):
        """
        场景：获取枚举值
        WHEN: 输入枚举类
        THEN: 返回值列表
        """
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        result = get_enum_values(Status)
        assert result == ["active", "inactive"]

    def test_is_valid_enum_value(self):
        """
        场景：验证枚举值
        WHEN: 输入有效/无效值
        THEN: 返回正确结果
        """
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"

        assert is_valid_enum_value("active", Status) is True
        assert is_valid_enum_value("invalid", Status) is False

    def test_enum_to_dict(self):
        """
        场景：枚举转字典
        WHEN: 输入枚举类
        THEN: 返回 {name: value} 字典
        """
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        result = enum_to_dict(Status)
        assert result == {"ACTIVE": "active", "INACTIVE": "inactive"}


class TestDictionaryUtil:
    """字典工具测试"""

    def test_deep_merge(self):
        """
        场景：深度合并
        WHEN: 合并嵌套字典
        THEN: 正确合并
        """
        base = {"user": {"name": "John", "age": 20}}
        override = {"user": {"age": 25}}
        result = deep_merge(base, override)
        assert result == {"user": {"name": "John", "age": 25}}

    def test_get_nested_value(self):
        """
        场景：获取嵌套值
        WHEN: 输入路径
        THEN: 返回值
        """
        data = {"user": {"profile": {"name": "John"}}}
        result = get_nested_value(data, "user.profile.name")
        assert result == "John"

    def test_get_nested_value_default(self):
        """
        场景：路径不存在
        WHEN: 路径无效
        THEN: 返回默认值
        """
        data = {"user": {}}
        result = get_nested_value(data, "user.name", default="Unknown")
        assert result == "Unknown"

    def test_set_nested_value(self):
        """
        场景：设置嵌套值
        WHEN: 设置深层路径
        THEN: 正确设置
        """
        data = {}
        set_nested_value(data, "user.profile.name", "John")
        assert data == {"user": {"profile": {"name": "John"}}}

    def test_flatten_dict(self):
        """
        场景：扁平化字典
        WHEN: 输入嵌套字典
        THEN: 返回扁平字典
        """
        data = {"user": {"name": "John", "age": 20}}
        result = flatten_dict(data)
        assert result == {"user.name": "John", "user.age": 20}


class TestJsonUtil:
    """JSON 工具测试"""

    def test_json_dumps_datetime(self):
        """
        场景：序列化 datetime
        WHEN: 输入包含 datetime 的对象
        THEN: 正确序列化
        """
        data = {"created_at": datetime(2024, 1, 15, 10, 30, 45)}
        result = json_dumps(data)
        assert "2024-01-15T10:30:45" in result

    def test_json_loads(self):
        """
        场景：解析 JSON
        WHEN: 输入 JSON 字符串
        THEN: 返回对象
        """
        result = json_loads('{"name": "John", "age": 30}')
        assert result == {"name": "John", "age": 30}

    def test_json_loads_bytes(self):
        """
        场景：解析字节
        WHEN: 输入字节
        THEN: 返回对象
        """
        result = json_loads(b'{"name": "John"}')
        assert result == {"name": "John"}
