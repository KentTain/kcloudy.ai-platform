## ADDED Requirements

### Requirement: PropertyMixin 提供属性容器通用字段

framework/database/mixins/property.py SHALL 提供 `PropertyMixin`，包含以下字段：
- `name`: String(256), NOT NULL, comment="名称"
- `display_name`: String(512), nullable, comment="显示名称"
- `description`: String(4000), nullable, comment="描述"
- `can_edit`: bool, default=True, comment="是否能编辑"
- `is_require`: bool, default=False, comment="是否必须"
- `index`: int, default=0, comment="排序"

#### Scenario: 模型继承 PropertyMixin 后自动拥有属性容器字段

- **WHEN** 一个 SQLAlchemy 模型继承 `PropertyMixin`
- **THEN** 该模型自动拥有 name、display_name、description、can_edit、is_require、index 列

#### Scenario: PropertyMixin 默认值正确

- **WHEN** 创建一个继承 PropertyMixin 的模型实例且未指定 can_edit/is_require/index
- **THEN** can_edit 为 True、is_require 为 False、index 为 0

### Requirement: PropertyAttributeMixin 提供属性值通用字段

framework/database/mixins/property.py SHALL 提供 `PropertyAttributeMixin`，包含以下字段：
- `data_type`: String(20), NOT NULL, default="string", comment="属性数据类型"
- `name`: String(256), NOT NULL, comment="属性值名称"
- `display_name`: String(512), nullable, comment="显示名称"
- `description`: String(4000), nullable, comment="描述"
- `value`: Text, nullable, comment="属性值"
- `ext_data`: JSONB, nullable, comment="扩展数据"
- `can_edit`: bool, default=True, comment="是否能编辑"
- `is_require`: bool, default=False, comment="是否必须"
- `index`: int, default=0, comment="排序"

#### Scenario: 模型继承 PropertyAttributeMixin 后自动拥有属性值字段

- **WHEN** 一个 SQLAlchemy 模型继承 `PropertyAttributeMixin`
- **THEN** 该模型自动拥有 data_type、name、display_name、description、value、ext_data、can_edit、is_require、index 列

#### Scenario: ext_data 存储 JSONB 替代 Ext1-3

- **WHEN** 一个属性值需要存储额外结构化数据（如加密方式、过期时间、选项列表）
- **THEN** ext_data JSONB 列可以存储任意结构化 JSON 数据，替代 .NET 的 Ext1/Ext2/Ext3 三个扁平字段

#### Scenario: ext_data 为空时不影响主值

- **WHEN** 一个属性值只有简单的 value，不需要扩展数据
- **THEN** ext_data 为 NULL，不影响 value 的正常使用

### Requirement: AttributeDataType 枚举定义属性数据类型

framework/database/mixins/property.py SHALL 定义 `AttributeDataType(str, Enum)` 枚举，包含以下值：
- STRING = "string"
- INTEGER = "integer"
- DECIMAL = "decimal"
- DATE_TIME = "date_time"
- BOOLEAN = "boolean"
- JSON = "json"

#### Scenario: AttributeDataType 直接继承 str 和 Enum

- **WHEN** 检查 AttributeDataType 的基类
- **THEN** 它继承 `(str, Enum)`，不继承 EnumBase（因为 framework 不依赖业务模块的 EnumBase）

#### Scenario: data_type 列存储枚举的字符串值

- **WHEN** 设置 PropertyAttributeMixin 的 data_type 为 AttributeDataType.INTEGER
- **THEN** 数据库存储值为 "integer"（字符串），不存储枚举对象

### Requirement: PropertyUtil 提供属性取值和类型转换工具

framework/utils/property_util.py SHALL 提供 `PropertyUtil` 类，包含以下静态方法：
- `get_attribute_by_name(attributes, name)`: 按名称获取属性对象，返回 None 如果未找到
- `get_value_by_name(attributes, name, default="")`: 按名称获取属性值（字符串形式）
- `get_values_by_name(attributes, name)`: 按名称获取所有匹配属性值列表
- `get_typed_value(attributes, name, target_type, default=None)`: 按名称获取类型化值
- `coerce_value(value, data_type)`: 将字符串值按 AttributeDataType 转换为对应 Python 类型

#### Scenario: coerce_value 按 data_type 转换类型

- **WHEN** 调用 `PropertyUtil.coerce_value("587", AttributeDataType.INTEGER)`
- **THEN** 返回整数 587

- **WHEN** 调用 `PropertyUtil.coerce_value("true", AttributeDataType.BOOLEAN)`
- **THEN** 返回布尔值 True

- **WHEN** 调用 `PropertyUtil.coerce_value("2026-05-24T10:00:00", AttributeDataType.DATE_TIME)`
- **THEN** 返回 datetime 对象

- **WHEN** 调用 `PropertyUtil.coerce_value('{"key":"val"}', AttributeDataType.JSON)`
- **THEN** 返回字典 {"key": "val"}

#### Scenario: coerce_value 类型转换失败时抛异常

- **WHEN** 调用 `PropertyUtil.coerce_value("abc", AttributeDataType.INTEGER)`
- **THEN** 抛出 ValueError 异常

#### Scenario: get_value_by_name 返回默认值

- **WHEN** 调用 `PropertyUtil.get_value_by_name(attributes, "nonexistent", default="default")`
- **THEN** 返回 "default"

### Requirement: framework/database 导出新增 Mixin 和枚举

framework/database/__init__.py SHALL 导出 PropertyMixin、PropertyAttributeMixin 和 AttributeDataType。

#### Scenario: 从 framework.database 导入 PropertyMixin

- **WHEN** 使用 `from framework.database import PropertyMixin`
- **THEN** 成功导入 PropertyMixin 类

#### Scenario: 从 framework.database 导入 AttributeDataType

- **WHEN** 使用 `from framework.database import AttributeDataType`
- **THEN** 成功导入 AttributeDataType 枚举