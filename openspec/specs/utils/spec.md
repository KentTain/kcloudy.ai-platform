## ADDED Requirements

### Requirement: 字符串工具函数
系统 SHALL 提供字符串处理工具函数，包括驼峰转换、截断、掩码等功能。

#### Scenario: 驼峰转下划线
- **WHEN** 调用 `to_snake_case("UserName")`
- **THEN** 返回 `"user_name"`

#### Scenario: 字符串掩码
- **WHEN** 调用 `mask_string("13812345678", start=3, end=7)`
- **THEN** 返回 `"138****5678"`

### Requirement: 时间日期工具函数
系统 SHALL 提供时间日期处理工具函数，支持格式化、解析、时区转换。

#### Scenario: 时间戳转日期
- **WHEN** 调用 `timestamp_to_datetime(1704067200)`
- **THEN** 返回对应的 datetime 对象

#### Scenario: 日期格式化
- **WHEN** 调用 `format_datetime(dt, "%Y-%m-%d %H:%M:%S")`
- **THEN** 返回格式化的日期字符串

#### Scenario: 相对时间
- **WHEN** 调用 `humanize_time(dt)`
- **THEN** 返回 `"3 小时前"` 等人类可读格式

### Requirement: 枚举工具函数
系统 SHALL 提供枚举处理工具函数，支持获取枚举值列表、验证枚举值等。

#### Scenario: 获取枚举值列表
- **WHEN** 调用 `get_enum_values(StatusEnum)`
- **THEN** 返回 `["active", "inactive", "pending"]`

#### Scenario: 枚举值验证
- **WHEN** 调用 `is_valid_enum_value("active", StatusEnum)`
- **THEN** 返回 `True`

### Requirement: 字典工具函数
系统 SHALL 提供字典处理工具函数，支持深度合并、扁平化、键转换等。

#### Scenario: 深度合并字典
- **WHEN** 调用 `deep_merge({"a": 1}, {"b": 2})`
- **THEN** 返回 `{"a": 1, "b": 2}`

#### Scenario: 字典键转下划线
- **WHEN** 调用 `keys_to_snake_case({"userName": "test"})`
- **THEN** 返回 `{"user_name": "test"}`

### Requirement: JSON 工具函数
系统 SHALL 提供增强的 JSON 处理函数，支持日期序列化、宽松解析等。

#### Scenario: 日期序列化
- **WHEN** 调用 `json_dumps({"date": datetime.now()})`
- **THEN** 返回包含日期 ISO 格式的 JSON 字符串

#### Scenario: 宽松 JSON 解析
- **WHEN** 调用 `json_loads('{"name": "test",}')` (含尾随逗号)
- **THEN** 返回解析后的字典
