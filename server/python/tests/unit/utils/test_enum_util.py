"""enum_util 单元测试"""

import concurrent.futures

import pytest

from demo.models.enums import Status
from demo.utils.enum_util import EnumDataUtils, EnumMemberData


class TestEnumDataUtils:
    """EnumDataUtils 单元测试"""

    def test_not_instantiable(self):
        """测试类不可实例化"""
        with pytest.raises(TypeError, match="This class is not instantiable"):
            EnumDataUtils()

    def test_get_enum_data(self):
        """测试获取单个枚举数据"""
        status_data = EnumDataUtils.get_enum_data("Status")
        expected_status: list[EnumMemberData] = [
            {"name": "DISABLE", "value": "0", "label": "禁用"},
            {"name": "ENABLE", "value": "1", "label": "启用"},
        ]
        assert status_data == expected_status

    def test_get_enum_data_not_found(self):
        """测试获取不存在的枚举数据"""
        result = EnumDataUtils.get_enum_data("NonExistent")
        assert result is None

    def test_get_batch_enum_data(self):
        """测试批量获取枚举数据"""
        batch_data = EnumDataUtils.get_batch_enum_data("Status")

        assert "Status" in batch_data
        assert batch_data["Status"] is not None
        assert len(batch_data["Status"]) > 0

    def test_get_batch_enum_data_with_spaces(self):
        """测试批量获取枚举数据（带空格）"""
        batch_data = EnumDataUtils.get_batch_enum_data("Status")
        assert "Status" in batch_data

    def test_get_all_enum_data(self):
        """测试获取所有枚举数据"""
        all_enum_data = EnumDataUtils.get_all_enum_data()

        assert "Status" in all_enum_data

        # 验证返回的是深拷贝
        test_enum_data: list[EnumMemberData] = [
            {"name": "TEST", "value": "test", "label": "Test"}
        ]
        all_enum_data["TestKey"] = test_enum_data
        assert "TestKey" not in EnumDataUtils.ENUM_MAP

    def test_to_enum_by_name(self):
        """测试通过名称转换为枚举"""
        result = EnumDataUtils.to_enum(Status, "ENABLE")
        assert result == Status.ENABLE

    def test_to_enum_by_value(self):
        """测试通过值转换为枚举"""
        result = EnumDataUtils.to_enum(Status, "1")
        assert result == Status.ENABLE

    def test_to_enum_already_enum(self):
        """测试已经是枚举类型的值"""
        result = EnumDataUtils.to_enum(Status, Status.DISABLE)
        assert result == Status.DISABLE

    def test_to_enum_invalid_value(self):
        """测试无效值转换"""
        with pytest.raises(ValueError):
            EnumDataUtils.to_enum(Status, "INVALID")

    def test_thread_safety(self):
        """测试线程安全性"""
        # 重置初始化状态以测试线程安全
        EnumDataUtils._initialized = False

        def init_and_get():
            return EnumDataUtils.get_enum_data("Status")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: init_and_get(), range(10)))

        # 验证所有线程获取到相同的结果
        assert all(result == results[0] for result in results)

        # 确保只初始化了一次
        assert EnumDataUtils._initialized is True
