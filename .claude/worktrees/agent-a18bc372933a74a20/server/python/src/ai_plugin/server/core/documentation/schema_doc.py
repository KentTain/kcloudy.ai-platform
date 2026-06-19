from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel


class SchemaDoc:
    """架构文档类，用于保存模型的文档信息"""

    def __init__(
        self,
        cls: type[BaseModel],
        description: str,
        name: str | None = None,
        top: bool = False,
        ignore_fields: list[str] | None = None,
        outside_reference_fields: Mapping[str, type[BaseModel]] | None = None,
    ):
        """
        初始化架构文档

        Args:
            cls: BaseModel类型
            description: 架构描述
            name: 可选的架构名称
            top: 是否应该放在文档顶部
            ignore_fields: 在文档中忽略的字段名列表
            outside_reference_fields: 外部引用字段映射
        """
        self.cls = cls
        self.description = description
        self.name = name
        self.top = top
        self.ignore_fields = ignore_fields or []
        self.outside_reference_fields = outside_reference_fields or {}


# 全局类映射字典，用于存储所有已注册的架构文档
__cls_mapping__: dict[type[BaseModel], SchemaDoc] = {}


def docs(
    description: str,
    name: str | None = None,
    top: bool = False,
    ignore_fields: list[str] | None = None,
    outside_reference_fields: Mapping[str, type[BaseModel]] | None = None,
) -> Callable:
    """
    用于为类添加架构文档的装饰器

    Args:
        description: 架构的描述
        name: 架构名称的可选覆盖
        top: 该架构是否应该放在文档的顶部
        ignore_fields: 在文档中要忽略的字段名列表
        outside_reference_fields: 外部引用字段的可选映射

    Returns:
        装饰器函数
    """

    def decorator(cls_or_func: Any) -> Any:
        """
        装饰器内部函数

        Args:
            cls_or_func: 要装饰的类或函数

        Returns:
            装饰后的类或函数
        """
        # 检查cls_or_func是否是一个类
        if isinstance(cls_or_func, type):
            nonlocal name
            name = name or cls_or_func.__name__

            # 如果类还没有在映射中，则添加它
            if cls_or_func not in __cls_mapping__:
                __cls_mapping__[cls_or_func] = SchemaDoc(
                    cls_or_func,
                    description,
                    name,
                    top,
                    ignore_fields,
                    outside_reference_fields,
                )

            # 为类添加架构文档属性
            if not hasattr(cls_or_func, "__schema_docs__"):
                cls_or_func.__schema_docs__ = []
            cls_or_func.__schema_docs__.append(__cls_mapping__[cls_or_func])
            return cls_or_func

    return decorator


def get_schema_doc(cls: type[BaseModel]) -> SchemaDoc | None:
    """
    获取类的架构文档

    Args:
        cls: BaseModel类型

    Returns:
        架构文档或None
    """
    return __cls_mapping__.get(cls)


def list_schema_docs() -> list[SchemaDoc]:
    """
    列出所有架构文档

    Returns:
        所有架构文档的列表
    """
    return list(__cls_mapping__.values())
