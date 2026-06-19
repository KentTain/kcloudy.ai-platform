"""
属性值工具类

提供属性取值、提取和类型转换方法。
"""

import json
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from framework.database.mixins.property import AttributeDataType


class PropertyUtil:
    """
    属性值工具类

    提供属性取值、提取和类型转换的静态方法。
    """

    @staticmethod
    def get_attribute_by_name(
        attributes: Sequence[Any],
        name: str
    ) -> Any | None:
        """
        按名称获取属性对象

        Args:
            attributes: 属性列表
            name: 属性名称

        Returns:
            匹配的属性对象，未找到返回 None
        """
        for attr in attributes:
            attr_name = attr.name if hasattr(attr, "name") else attr.get("name")
            if attr_name == name:
                return attr
        return None

    @staticmethod
    def get_value_by_name(
        attributes: Sequence[Any],
        name: str,
        default: str = ""
    ) -> str:
        """
        按名称获取属性值（字符串形式）

        Args:
            attributes: 属性列表
            name: 属性名称
            default: 默认值

        Returns:
            属性值字符串，未找到返回默认值
        """
        attr = PropertyUtil.get_attribute_by_name(attributes, name)
        if attr is None:
            return default

        value = attr.value if hasattr(attr, "value") else attr.get("value")
        return str(value) if value is not None else default

    @staticmethod
    def get_values_by_name(
        attributes: Sequence[Any],
        name: str
    ) -> list[str]:
        """
        按名称获取所有匹配属性值列表

        Args:
            attributes: 属性列表
            name: 属性名称

        Returns:
            匹配的属性值列表
        """
        values = []
        for attr in attributes:
            attr_name = attr.name if hasattr(attr, "name") else attr.get("name")
            if attr_name == name:
                value = attr.value if hasattr(attr, "value") else attr.get("value")
                if value is not None:
                    values.append(str(value))
        return values

    @staticmethod
    def get_typed_value(
        attributes: Sequence[Any],
        name: str,
        target_type: type,
        default: Any = None
    ) -> Any:
        """
        按名称获取类型化值

        Args:
            attributes: 属性列表
            name: 属性名称
            target_type: 目标类型
            default: 默认值

        Returns:
            类型转换后的值
        """
        attr = PropertyUtil.get_attribute_by_name(attributes, name)
        if attr is None:
            return default

        value = attr.value if hasattr(attr, "value") else attr.get("value")
        if value is None:
            return default

        data_type = attr.data_type if hasattr(attr, "data_type") else attr.get("data_type")
        if data_type:
            try:
                attr_data_type = AttributeDataType(data_type)
                return PropertyUtil.coerce_value(str(value), attr_data_type)
            except ValueError:
                pass

        try:
            return target_type(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def coerce_value(
        value: str,
        data_type: AttributeDataType
    ) -> Any:
        """
        将字符串值按 AttributeDataType 转换为对应 Python 类型

        Args:
            value: 字符串值
            data_type: 属性数据类型

        Returns:
            类型转换后的值

        Raises:
            ValueError: 类型转换失败时抛出
        """
        if value is None:
            return None

        if data_type == AttributeDataType.STRING:
            return value

        if data_type == AttributeDataType.INTEGER:
            return int(value)

        if data_type == AttributeDataType.DECIMAL:
            try:
                return Decimal(value)
            except Exception as e:
                raise ValueError(f"无法解析小数: {value}") from e

        if data_type == AttributeDataType.DATE_TIME:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"无法解析日期时间: {value}")

        if data_type == AttributeDataType.BOOLEAN:
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            if value.lower() in ("false", "0", "no", "off"):
                return False
            raise ValueError(f"无法解析布尔值: {value}")

        if data_type == AttributeDataType.JSON:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 解析失败: {value}") from e

        return value
