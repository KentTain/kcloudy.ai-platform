"""
基础 Schema 模型类

提供统一的 Pydantic 模型基类。
"""

import warnings
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
)

from extended.fastapi.responses import ORJSONResponse


class Success(ORJSONResponse):
    """成功响应"""

    def __init__(
        self,
        code: int = HTTP_200_OK,
        msg: str | None = "OK",
        data: Any | None = None,
        **kwargs,
    ) -> None:
        """
        初始化实例。

        Args:
            code (int): code 参数。
            msg (str | None): msg 参数。
            data (Any | None): data 参数。
            kwargs: kwargs 参数。
        """
        content: dict[str, Any] = {
            "code": code,
            "msg": msg,
            "data": data,
        }
        # 添加额外的参数，如conversation_id, has_more, limit等
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class SuccessExtra(ORJSONResponse):
    """分页成功响应"""

    def __init__(
        self,
        code: int = HTTP_200_OK,
        msg: str | None = None,
        data: Any | None = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ) -> None:
        """
        初始化实例。

        Args:
            code (int): code 参数。
            msg (str | None): msg 参数。
            data (Any | None): data 参数。
            total (int): total 参数。
            page (int): page 参数。
            page_size (int): page_size 参数。
            kwargs: kwargs 参数。
        """
        content: dict[str, Any] = {
            "code": code,
            "msg": msg,
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        content.update(kwargs)
        super().__init__(
            content=content,
            status_code=code,
        )


class Fail(ORJSONResponse):
    """失败响应"""

    def __init__(
        self,
        code: int = HTTP_400_BAD_REQUEST,
        msg: str | None = None,
        data: Any | None = None,
        **kwargs,
    ) -> None:
        """
        初始化实例。

        Args:
            code (int): code 参数。
            msg (str | None): msg 参数。
            data (Any | None): data 参数。
            kwargs: kwargs 参数。
        """
        content: dict[str, Any] = {
            "code": code,
            "msg": msg,
            "data": data,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class BaseModel(PydanticBaseModel):
    """拓展Pydantic基础模型类"""

    model_config = ConfigDict(
        # 时间序列化格式
        ser_json_timedelta="iso8601",
        # 从属性中获取模型数据，方便ORM模型转换
        from_attributes=True,
        # 允许通过字段名称和别名(alias)来填充数据
        populate_by_name=True,
        # 使用枚举值而非枚举对象，使序列化更直观
        use_enum_values=True,
        # 验证默认值，确保默认值也符合字段约束
        validate_default=True,
        # JSON输出时处理无穷大和NaN值
        ser_json_inf_nan="null",
        # 字符串处理选项
        str_strip_whitespace=True,
        # 字符串缓存，提高性能
        cache_strings=True,
        # 支持中文注释文档
        use_attribute_docstrings=True,
        # 处理额外字段的策略
        extra="ignore",
    )


class BaseQuery(BaseModel):
    """列表查询基类，仅包含通用过滤字段"""

    keyword: str | None = Field(default=None, description="搜索关键词")


class BasePaginatedQuery(BaseQuery):
    """分页查询基类，继承 BaseQuery 并添加分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class BaseQueryParams(BaseModel):
    """基础查询参数Schema

    .. deprecated::
        使用 BaseQuery 或 BasePaginatedQuery 替代。
        BaseQueryParams 将在未来版本中移除。
    """

    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=20, description="每页条数")

    def __init__(self, **data):
        warnings.warn(
            "BaseQueryParams 已废弃，请使用 BaseQuery 或 BasePaginatedQuery 替代",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)

    def __init_subclass__(cls, **kwargs):
        warnings.warn(
            "BaseQueryParams 已废弃，请使用 BaseQuery 或 BasePaginatedQuery 替代",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init_subclass__(**kwargs)


class VoMixin(BaseModel):
    """VO模型基类"""

    @classmethod
    def get_model_class(
        cls, target_cls: type["VoMixin"] | None = None
    ) -> type["VoMixin"]:
        """获取模型类"""
        if target_cls is not None:
            return target_cls
        return cls


class TreeNodeVoMixin(VoMixin):
    """
    树结构拓展

    提供树形结构数据支持：
    1. 父子关系
    2. 层级管理
    3. 排序功能
    4. 路径追踪
    """

    parent_id: str | None = Field(default=None, description="父级id")
    parent_ids: str | None = Field(description="全父级id")
    tree_leaf: bool = Field(default=False, description="是否叶末")
    tree_level: int = Field(default=0, description="深度层级")
    tree_sort: int = Field(default=0, description="排序号")
    tree_sorts: str = Field(default="0", description="多级排序号")
    tree_names: str | None = Field(description="全节点名")


class AuditedOperatorVoMixin(VoMixin):
    """
    审计操作人拓展

    提供操作人审计功能：
    1. 创建人
    2. 创建时间
    3. 更新人
    4. 更新时间
    5. 删除时间（软删除）
    """

    created_by: str = Field(description="创建人id")
    created_at: datetime = Field(description="创建时间")
    updated_by: str = Field(description="修改人id")
    updated_at: datetime = Field(description="修改时间")
    deleted_at: datetime = Field(description="删除时间")

    @staticmethod
    def get_beijing_time():
        """获取当前北京时间"""
        utc_now = datetime.now(UTC)
        beijing_tz = timezone(timedelta(hours=8))
        return utc_now.astimezone(beijing_tz)


class PropertyVoMixin(VoMixin):
    """
    属性容器 VO Mixin

    对应 ORM 层 PropertyMixin，提供属性容器的通用字段。
    """

    name: str = Field(description="名称")
    display_name: str | None = Field(default=None, description="显示名称")
    description: str | None = Field(default=None, description="描述")
    can_edit: bool = Field(default=True, description="是否能编辑")
    is_require: bool = Field(default=False, description="是否必须")
    index: int = Field(default=0, description="排序")


class PropertyAttributeVoMixin(VoMixin):
    """
    属性值 VO Mixin

    对应 ORM 层 PropertyAttributeMixin，提供属性值的通用字段。
    """

    data_type: str = Field(default="string", description="属性数据类型")
    name: str = Field(description="属性值名称")
    display_name: str | None = Field(default=None, description="显示名称")
    description: str | None = Field(default=None, description="描述")
    value: str | None = Field(default=None, description="属性值")
    ext_data: dict[str, Any] | None = Field(default=None, description="扩展数据")
    can_edit: bool = Field(default=True, description="是否能编辑")
    is_require: bool = Field(default=False, description="是否必须")
    index: int = Field(default=0, description="排序")


class I18nConvertibleBaseModel(BaseModel):
    """
    支持I18nObject自动转换的基础模型类

    继承此类的模型在序列化时会自动将所有嵌套的I18nObject转换为字符串
    转换规则：优先使用中文（zh_Hans），没有中文则使用英文（en_US）
    """

    def _convert_i18n_to_string(self, obj: Any) -> Any:
        """
        递归地将所有I18nObject转换为字符串
        """
        from ai_plugin.sdk.entities import I18nObject

        if isinstance(obj, I18nObject):
            return obj.zh_Hans if obj.zh_Hans else obj.en_US

        elif isinstance(obj, dict):
            return {
                key: self._convert_i18n_to_string(value) for key, value in obj.items()
            }

        elif isinstance(obj, list | tuple):
            converted = [self._convert_i18n_to_string(item) for item in obj]
            return converted if isinstance(obj, list) else tuple(converted)

        elif isinstance(obj, set):
            return {self._convert_i18n_to_string(item) for item in obj}

        elif hasattr(obj, "model_dump") and not isinstance(obj, type(self)):
            try:
                return self._convert_pydantic_model_fields(obj)
            except Exception:
                try:
                    return self._convert_i18n_to_string(obj.__dict__)
                except Exception:
                    return obj

        elif isinstance(obj, Enum):
            return self._convert_i18n_to_string(obj.value)

        elif hasattr(obj, "__dict__"):
            try:
                return self._convert_i18n_to_string(obj.__dict__)
            except Exception:
                return obj

        else:
            return obj

    def _convert_pydantic_model_fields(self, obj: Any) -> dict[str, Any]:
        """转换 Pydantic 模型的字段，保持字段类型信息"""
        result = {}

        if hasattr(obj, "model_fields"):
            for field_name in obj.model_fields:
                field_value = getattr(obj, field_name, None)
                result[field_name] = self._convert_i18n_to_string(field_value)
        else:
            for key, value in obj.__dict__.items():
                result[key] = self._convert_i18n_to_string(value)

        return result

    def model_dump(
        self,
        *,
        include: set | dict | None = None,
        exclude: set | dict | None = None,
        context: dict | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        mode: str = "python",
        serialize_as_any: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """重写model_dump方法，在序列化时自动转换所有嵌套的I18nObject为字符串"""
        raw_data = {}

        for field_name in self.model_fields:
            if include is not None and field_name not in include:
                continue
            if exclude is not None and field_name in exclude:
                continue

            field_value = getattr(self, field_name, None)

            if exclude_unset and field_name not in self.model_fields_set:
                continue
            if (
                exclude_defaults
                and field_value == self.model_fields[field_name].default
            ):
                continue
            if exclude_none and field_value is None:
                continue

            raw_data[field_name] = self._convert_i18n_to_string(field_value)

        return raw_data


__all__ = [
    "BaseModel",
    "BaseQuery",
    "BasePaginatedQuery",
    "BaseQueryParams",  # deprecated, use BaseQuery or BasePaginatedQuery
    "VoMixin",
    "TreeNodeVoMixin",
    "AuditedOperatorVoMixin",
    "PropertyVoMixin",
    "PropertyAttributeVoMixin",
    "I18nConvertibleBaseModel",
]
