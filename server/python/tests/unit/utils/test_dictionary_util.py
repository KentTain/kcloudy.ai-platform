"""dictionary_util 单元测试"""

import pytest

from demo.utils.dictionary_util import deep_merge_dict


class TestDeepMergeDict:
    """deep_merge_dict 单元测试"""

    def test_merge_flat_dictionaries(self):
        """测试合并扁平字典"""
        result = deep_merge_dict({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_merge_nested_dictionaries(self):
        """测试合并嵌套字典"""
        result = deep_merge_dict({"a": {"b": 1}}, {"a": {"c": 2}})
        assert result == {"a": {"b": 1, "c": 2}}

    def test_overwrite_non_dict_values(self):
        """测试覆盖非字典值"""
        result = deep_merge_dict({"a": 1}, {"a": 2})
        assert result == {"a": 2}

    def test_merge_with_empty_dict(self):
        """测试与空字典合并"""
        result = deep_merge_dict({"a": 1}, {})
        assert result == {"a": 1}

        result = deep_merge_dict({}, {"b": 2})
        assert result == {"b": 2}

    def test_deep_nested_merge(self):
        """测试深度嵌套合并"""
        result = deep_merge_dict(
            {"a": {"b": {"c": 1}}},
            {"a": {"b": {"d": 2}}},
        )
        assert result == {"a": {"b": {"c": 1, "d": 2}}}

    def test_original_dicts_not_modified(self):
        """测试原字典不被修改"""
        x = {"a": {"b": 1}}
        y = {"a": {"c": 2}}
        result = deep_merge_dict(x, y)
        assert x == {"a": {"b": 1}}
        assert y == {"a": {"c": 2}}
        assert result == {"a": {"b": 1, "c": 2}}

    def test_mixed_value_types(self):
        """测试混合值类型"""
        result = deep_merge_dict(
            {"a": {"b": 1, "c": "text"}},
            {"a": {"d": [1, 2, 3]}},
        )
        assert result == {"a": {"b": 1, "c": "text", "d": [1, 2, 3]}}
