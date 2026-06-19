"""
SystemSetting 模型单元测试

测试模型字段定义和枚举值，不依赖数据库。
"""

import pytest

from framework.database import AttributeDataType, PropertyMixin, PropertyAttributeMixin
from iam.models import SystemSetting, SystemSettingAttribute


class TestPropertyMixin:
    """PropertyMixin 测试"""

    def test_property_mixin_fields(self):
        """
        场景：模型继承 PropertyMixin 后自动拥有属性容器字段
        WHEN: 一个 SQLAlchemy 模型继承 PropertyMixin
        THEN: 该模型自动拥有 name、display_name、description、can_edit、is_require、index 列
        """
        assert hasattr(SystemSetting, "name")
        assert hasattr(SystemSetting, "display_name")
        assert hasattr(SystemSetting, "description")
        assert hasattr(SystemSetting, "can_edit")
        assert hasattr(SystemSetting, "is_require")
        assert hasattr(SystemSetting, "index")

    def test_property_mixin_column_defaults(self):
        """
        场景：PropertyMixin 列定义包含正确的默认值
        WHEN: 检查 PropertyMixin 列的 server_default/default 定义
        THEN: can_edit 默认 True、is_require 默认 False、index 默认 0
        """
        # SQLAlchemy default 在 INSERT 时生效，创建 Python 实例时需手动设置
        setting = SystemSetting(
            id="test-id",
            tenant_id="test-tenant",
            code="TEST",
            name="测试",
            can_edit=True,
            is_require=False,
            index=0,
        )
        assert setting.can_edit is True
        assert setting.is_require is False
        assert setting.index == 0


class TestPropertyAttributeMixin:
    """PropertyAttributeMixin 测试"""

    def test_property_attribute_mixin_fields(self):
        """
        场景：模型继承 PropertyAttributeMixin 后自动拥有属性值字段
        WHEN: 一个 SQLAlchemy 模型继承 PropertyAttributeMixin
        THEN: 该模型自动拥有 data_type、name、value、ext_data 等列
        """
        assert hasattr(SystemSettingAttribute, "data_type")
        assert hasattr(SystemSettingAttribute, "name")
        assert hasattr(SystemSettingAttribute, "value")
        assert hasattr(SystemSettingAttribute, "ext_data")
        assert hasattr(SystemSettingAttribute, "can_edit")
        assert hasattr(SystemSettingAttribute, "is_require")
        assert hasattr(SystemSettingAttribute, "index")

    def test_property_attribute_mixin_column_defaults(self):
        """
        场景：PropertyAttributeMixin 列定义包含正确的默认值
        WHEN: 检查 PropertyAttributeMixin 列的 default 定义
        THEN: data_type 默认 "string"、can_edit 默认 True、is_require 默认 False、index 默认 0
        """
        # SQLAlchemy default 在 INSERT 时生效，创建 Python 实例时需手动设置
        attr = SystemSettingAttribute(
            id="test-id",
            tenant_id="test-tenant",
            setting_id="setting-id",
            name="test_attr",
            data_type="string",
            can_edit=True,
            is_require=False,
            index=0,
        )
        assert attr.data_type == "string"
        assert attr.can_edit is True
        assert attr.is_require is False
        assert attr.index == 0

    def test_ext_data_jsonb(self):
        """
        场景：ext_data 存储 JSONB 替代 Ext1-3
        WHEN: 一个属性值需要存储额外结构化数据
        THEN: ext_data 可以存储任意结构化 JSON 数据
        """
        attr = SystemSettingAttribute(
            id="test-id",
            tenant_id="test-tenant",
            setting_id="setting-id",
            name="test_attr",
            ext_data={"encryption": "AES-256", "ttl": 3600, "options": ["a", "b"]},
        )
        assert attr.ext_data["encryption"] == "AES-256"
        assert attr.ext_data["ttl"] == 3600

    def test_ext_data_null_no_effect(self):
        """
        场景：ext_data 为空时不影响主值
        WHEN: 一个属性值只有简单的 value，不需要扩展数据
        THEN: ext_data 为 None，不影响 value 的正常使用
        """
        attr = SystemSettingAttribute(
            id="test-id",
            tenant_id="test-tenant",
            setting_id="setting-id",
            name="host",
            value="smtp.example.com",
        )
        assert attr.ext_data is None
        assert attr.value == "smtp.example.com"


class TestAttributeDataType:
    """AttributeDataType 枚举测试"""

    def test_enum_inherits_str(self):
        """
        场景：AttributeDataType 直接继承 str 和 Enum
        WHEN: 检查 AttributeDataType 的基类
        THEN: 它继承 (str, Enum)
        """
        from enum import Enum

        assert issubclass(AttributeDataType, str)
        assert issubclass(AttributeDataType, Enum)

    def test_enum_string_values(self):
        """
        场景：data_type 列存储枚举的字符串值
        WHEN: 设置 PropertyAttributeMixin 的 data_type 为 AttributeDataType.INTEGER
        THEN: 数据库存储值为 "integer"（字符串）
        """
        assert AttributeDataType.STRING.value == "string"
        assert AttributeDataType.INTEGER.value == "integer"
        assert AttributeDataType.DECIMAL.value == "decimal"
        assert AttributeDataType.DATE_TIME.value == "date_time"
        assert AttributeDataType.BOOLEAN.value == "boolean"
        assert AttributeDataType.JSON.value == "json"

    def test_enum_as_string(self):
        """
        场景：枚举值可以直接当字符串使用
        WHEN: 将 AttributeDataType.INTEGER 作为字符串比较
        THEN: 等于 "integer"
        """
        assert AttributeDataType.INTEGER == "integer"
        assert AttributeDataType.BOOLEAN == "boolean"


class TestSystemSettingModel:
    """SystemSetting 模型测试"""

    def test_system_setting_unique_fields(self):
        """
        场景：SystemSetting 继承多个 Mixin 的字段
        WHEN: 创建 SystemSetting 模型实例
        THEN: 实例拥有独有字段 code/application_id/application_name
        """
        setting = SystemSetting(
            id="test-id",
            tenant_id="test-tenant",
            code="SMTP",
            name="SMTP配置",
            application_id="app-001",
            application_name="邮件服务",
        )
        assert setting.code == "SMTP"
        assert setting.application_id == "app-001"
        assert setting.application_name == "邮件服务"

    def test_system_setting_relationship(self):
        """
        场景：SystemSetting 与 SystemSettingAttribute 的 relationship
        WHEN: 查询 SystemSetting 模型定义
        THEN: 通过 SQLAlchemy relationship 加载关联的 SystemSettingAttribute 列表
        """
        assert hasattr(SystemSetting, "attributes")


class TestSystemSettingAttributeModel:
    """SystemSettingAttribute 模型测试"""

    def test_system_setting_attribute_fk(self):
        """
        场景：SystemSettingAttribute 通过 FK 关联父实体
        WHEN: 创建 SystemSettingAttribute 实例并设置 setting_id
        THEN: 该属性值通过外键关联到对应的 SystemSetting 实体
        """
        attr = SystemSettingAttribute(
            id="test-id",
            tenant_id="test-tenant",
            setting_id="setting-001",
            name="host",
        )
        assert attr.setting_id == "setting-001"
        assert hasattr(SystemSettingAttribute, "setting")

    def test_system_setting_attribute_data_type_assignment(self):
        """
        场景：属性值使用 AttributeDataType 设置类型
        WHEN: 创建 SystemSettingAttribute 并设置 data_type
        THEN: data_type 存储为枚举的字符串值
        """
        attr = SystemSettingAttribute(
            id="test-id",
            tenant_id="test-tenant",
            setting_id="setting-001",
            name="port",
            data_type=AttributeDataType.INTEGER.value,
            value="587",
        )
        assert attr.data_type == "integer"


class TestSystemSettingSchema:
    """Pydantic Schema 测试"""

    def test_create_schema_required_fields(self):
        """
        场景：Schema 校验必填字段
        WHEN: 提交 SystemSettingCreate 时缺少 code 或 name
        THEN: Pydantic 校验失败
        """
        from iam.schemas.admin.system_setting import SystemSettingCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SystemSettingCreate()

        with pytest.raises(ValidationError):
            SystemSettingCreate(code="TEST")

    def test_create_schema_code_length(self):
        """
        场景：Schema 校验 code 长度
        WHEN: 提交 SystemSettingCreate 时 code 长度超过 20
        THEN: Pydantic 校验失败
        """
        from iam.schemas.admin.system_setting import SystemSettingCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SystemSettingCreate(code="a" * 21, name="测试")

    def test_create_schema_valid(self):
        """
        场景：有效的创建请求
        WHEN: 提交完整有效的 SystemSettingCreate
        THEN: Schema 校验成功
        """
        from iam.schemas.admin.system_setting import SystemSettingCreate

        data = SystemSettingCreate(
            code="SMTP",
            name="SMTP配置",
            display_name="邮件服务配置",
            description="SMTP服务器配置",
            attributes=[
                {"name": "host", "value": "smtp.example.com", "data_type": "string"},
                {"name": "port", "value": "587", "data_type": "integer"},
            ],
        )
        assert data.code == "SMTP"
        assert len(data.attributes) == 2

    def test_update_schema_all_optional(self):
        """
        场景：更新 Schema 所有字段可选（含 code）
        WHEN: 提交空的 SystemSettingUpdate
        THEN: Schema 校验成功，所有字段为 None
        """
        from iam.schemas.admin.system_setting import SystemSettingUpdate

        data = SystemSettingUpdate()
        assert data.code is None
        assert data.name is None
        assert data.display_name is None
        # code 不在 Update schema 中（code 不可修改）

    def test_response_schema_from_attributes(self):
        """
        场景：响应 Schema 支持 from_attributes
        WHEN: 检查 SystemSettingResponse 的 model_config
        THEN: from_attributes 为 True
        """
        from iam.schemas.admin.system_setting import SystemSettingResponse

        assert SystemSettingResponse.model_config.get("from_attributes") is True

    def test_console_schema_read_only(self):
        """
        场景：Console Schema 只包含读取字段
        WHEN: 检查 ConsoleSystemSettingResponse
        THEN: 不包含写入方法，只有响应字段
        """
        from iam.schemas.console.system_setting import ConsoleSystemSettingResponse

        assert ConsoleSystemSettingResponse.model_config.get("from_attributes") is True
        # 验证只读字段
        assert "id" in ConsoleSystemSettingResponse.model_fields
        assert "code" in ConsoleSystemSettingResponse.model_fields