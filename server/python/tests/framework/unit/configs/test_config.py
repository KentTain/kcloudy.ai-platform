"""
config 模块单元测试
"""


import pytest

from framework.configs.base import BaseSettings
from framework.configs.helpers import (
    convert_dict_hyphen_to_underscore,
    deep_merge_dict,
    hyphen_to_underscore,
)


class TestHyphenToUnderscore:
    """hyphen_to_underscore 函数测试"""

    def test_simple_conversion(self):
        """
        场景：简单转换
        WHEN: 输入 "user-name"
        THEN: 返回 "user_name"
        """
        result = hyphen_to_underscore("user-name")
        assert result == "user_name"

    def test_multiple_hyphens(self):
        """
        场景：多个连字符
        WHEN: 输入 "user-full-name"
        THEN: 返回 "user_full_name"
        """
        result = hyphen_to_underscore("user-full-name")
        assert result == "user_full_name"

    def test_no_hyphen(self):
        """
        场景：无连字符
        WHEN: 输入 "username"
        THEN: 返回原字符串
        """
        result = hyphen_to_underscore("username")
        assert result == "username"

    def test_none_input(self):
        """
        场景：None 输入
        WHEN: 输入 None
        THEN: 返回 None
        """
        result = hyphen_to_underscore(None)
        assert result is None

    def test_non_string_input(self):
        """
        场景：非字符串输入
        WHEN: 输入数字
        THEN: 返回原值
        """
        result = hyphen_to_underscore(123)
        assert result == 123


class TestConvertDictHyphenToUnderscore:
    """convert_dict_hyphen_to_underscore 函数测试"""

    def test_simple_dict(self):
        """
        场景：简单字典
        WHEN: 输入 {"user-name": "test"}
        THEN: 返回 {"user_name": "test"}
        """
        result = convert_dict_hyphen_to_underscore({"user-name": "test"})
        assert result == {"user_name": "test"}

    def test_nested_dict(self):
        """
        场景：嵌套字典
        WHEN: 输入嵌套字典
        THEN: 所有键名转换
        """
        data = {
            "user-info": {
                "full-name": "John"
            }
        }
        result = convert_dict_hyphen_to_underscore(data)
        assert result == {"user_info": {"full_name": "John"}}

    def test_list_in_dict(self):
        """
        场景：字典中的列表
        WHEN: 输入包含列表的字典
        THEN: 列表元素也转换
        """
        data = {
            "user-list": [
                {"user-name": "John"},
                {"user-name": "Jane"}
            ]
        }
        result = convert_dict_hyphen_to_underscore(data)
        assert result == {
            "user_list": [
                {"user_name": "John"},
                {"user_name": "Jane"}
            ]
        }

    def test_none_input(self):
        """
        场景：None 输入
        WHEN: 输入 None
        THEN: 返回 None
        """
        result = convert_dict_hyphen_to_underscore(None)
        assert result is None


class TestDeepMergeDict:
    """deep_merge_dict 函数测试"""

    def test_simple_merge(self):
        """
        场景：简单合并
        WHEN: 合并两个字典
        THEN: 返回合并结果
        """
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge_dict(base, override)
        assert result == {"a": 1, "b": 2}

    def test_nested_merge(self):
        """
        场景：嵌套合并
        WHEN: 合并嵌套字典
        THEN: 深度合并
        """
        base = {"user": {"name": "John", "age": 20}}
        override = {"user": {"age": 25}}
        result = deep_merge_dict(base, override)
        assert result == {"user": {"name": "John", "age": 25}}

    def test_override_value(self):
        """
        场景：覆盖值
        WHEN: 键相同
        THEN: 使用覆盖值
        """
        base = {"a": 1}
        override = {"a": 2}
        result = deep_merge_dict(base, override)
        assert result == {"a": 2}


class TestBaseSettings:
    """BaseSettings 类测试"""

    def test_from_dict(self):
        """
        场景：从字典创建
        WHEN: 传入有效字典
        THEN: 创建配置实例
        """
        class TestSettings(BaseSettings):
            name: str = "default"
            value: int = 0

        settings = TestSettings.from_dict({"name": "test", "value": 42})
        assert settings.name == "test"
        assert settings.value == 42

    def test_from_dict_with_hyphen_keys(self):
        """
        场景：连字符键名
        WHEN: 传入连字符键名
        THEN: 自动转换为下划线
        """
        class TestSettings(BaseSettings):
            user_name: str = "default"

        settings = TestSettings.from_dict({"user-name": "John"})
        assert settings.user_name == "John"

    def test_empty_dict_raises_error(self):
        """
        场景：空字典
        WHEN: 传入空字典
        THEN: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="配置字典不能为空"):
            BaseSettings.from_dict({})
