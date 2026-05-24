## ADDED Requirements

### Requirement: SystemSetting 模型定义租户级配置容器

iam/models/system_setting.py SHALL 定义 `SystemSetting` 模型，继承 `BaseModel` + `TenantMixin` + `PropertyMixin` + `ActiveRecordMixin`，表名 `system_settings`，包含以下独有字段：
- `code`: String(20), NOT NULL, comment="设置编号"
- `application_id`: String(36), nullable, comment="应用程序Id"
- `application_name`: String(128), nullable, comment="应用程序名称"

#### Scenario: SystemSetting 继承多个 Mixin 的字段

- **WHEN** 创建 SystemSetting 模型实例
- **THEN** 实例拥有 BaseModel 的 id/created_at/updated_at、TenantMixin 的 tenant_id、PropertyMixin 的 name/display_name/description/can_edit/is_require/index、ActiveRecordMixin 的 CRUD 方法，以及独有字段 code/application_id/application_name

#### Scenario: SystemSetting 与 SystemSettingAttribute 的 relationship

- **WHEN** 查询 SystemSetting 并访问其 attributes 属性
- **THEN** 通过 SQLAlchemy relationship 加载关联的 SystemSettingAttribute 列表，按 index 排序，使用 selectin 加载策略

### Requirement: SystemSettingAttribute 模型定义配置属性值

iam/models/system_setting_attribute.py SHALL 定义 `SystemSettingAttribute` 模型，继承 `BaseModel` + `TenantMixin` + `PropertyAttributeMixin`，表名 `system_setting_attributes`，包含以下独有字段：
- `setting_id`: String(36), ForeignKey("system_settings.id", ondelete="CASCADE"), NOT NULL, comment="配置Id"
- `setting`: relationship back_populates="attributes"，指向 SystemSetting

#### Scenario: SystemSettingAttribute 通过 FK 关联父实体

- **WHEN** 创建 SystemSettingAttribute 实例并设置 setting_id
- **THEN** 该属性值通过外键关联到对应的 SystemSetting 实体

#### Scenario: 删除 SystemSetting 时级联删除属性值

- **WHEN** 删除一个 SystemSetting 实体
- **THEN** 所有关联的 SystemSettingAttribute 实例自动被级联删除

### Requirement: 数据库约束保证数据完整性

SystemSetting 和 SystemSettingAttribute SHALL 定义以下约束：
- `uq_system_settings_tenant_code`: UNIQUE (tenant_id, code)，同一租户内设置编号唯一
- `uq_system_setting_attributes_setting_name`: UNIQUE (setting_id, name)，同一设置内属性名唯一
- `ix_system_settings_tenant_id`: INDEX (tenant_id)
- `ix_system_setting_attributes_setting_id`: INDEX (setting_id)
- `ix_system_setting_attributes_tenant_id`: INDEX (tenant_id)

#### Scenario: 同一租户内设置编号唯一

- **WHEN** 在同一 tenant_id 下创建两个 code 相同的 SystemSetting
- **THEN** 数据库抛出唯一约束冲突错误

#### Scenario: 不同租户可使用相同设置编号

- **WHEN** 在不同 tenant_id 下创建两个 code 相同的 SystemSetting
- **THEN** 创建成功，不冲突

#### Scenario: 同一设置内属性名唯一

- **WHEN** 在同一 setting_id 下创建两个 name 相同的 SystemSettingAttribute
- **THEN** 数据库抛出唯一约束冲突错误

### Requirement: 多租户数据隔离

SystemSetting 和 SystemSettingAttribute SHALL 都使用 TenantMixin，确保：
- TenantQueryInterceptor 自动按 tenant_id 过滤查询
- TenantEventListener 在插入时自动注入 tenant_id
- admin 跨租户查询通过 set_skip_tenant(True) 控制

#### Scenario: 普通用户只能看到本租户的配置

- **WHEN** 租户 A 的用户查询 SystemSetting 列表
- **THEN** TenantQueryInterceptor 自动添加 WHERE tenant_id = 'A'，只返回租户 A 的配置

#### Scenario: 管理员可跨租户查询配置

- **WHEN** 管理员调用 set_skip_tenant(True) 后查询 SystemSetting 列表
- **THEN** 返回所有租户的配置数据

#### Scenario: 新建配置自动注入租户ID

- **WHEN** 创建 SystemSetting 时未指定 tenant_id
- **THEN** TenantEventListener 从请求上下文自动注入当前租户ID

### Requirement: SystemSetting CRUD Service

iam/services/system_setting_service.py SHALL 提供 SystemSettingService，包含以下方法：
- `create_setting(session, data)`: 创建配置及其属性值
- `get_setting(session, id)`: 获取配置详情（含属性值）
- `update_setting(session, id, data)`: 更新配置及其属性值
- `delete_setting(session, id)`: 删除配置（级联删除属性值）
- `list_settings(session, fuzzy_fields)`: 列出配置（支持模糊搜索）
- `get_setting_by_code(session, code)`: 按编号获取配置

#### Scenario: 创建配置时同时创建属性值

- **WHEN** 调用 create_setting 传入 name="smtp配置"、code="SMTP" 和 attributes=[{name:"host", value:"smtp.example.com", data_type:"string"}, {name:"port", value:"587", data_type:"integer"}]
- **THEN** 创建 SystemSetting 和两个 SystemSettingAttribute，tenant_id 从上下文自动注入

#### Scenario: 更新配置时同步更新属性值

- **WHEN** 调用 update_setting 更新配置的 attributes 列表
- **THEN** 已有属性值更新、新增属性值创建、多余属性值删除

#### Scenario: 删除配置级联删除属性值

- **WHEN** 调用 delete_setting 删除一个 SystemSetting
- **THEN** 该配置和所有关联属性值一起删除

#### Scenario: 按编号获取配置

- **WHEN** 调用 get_setting_by_code(session, "SMTP")
- **THEN** 返回对应租户内 code 为 "SMTP" 的 SystemSetting（含属性值）

### Requirement: Admin API 端点

iam/controllers/admin/system_setting_controller.py SHALL 提供管理端 API：
- `POST /admin/v1/system-settings`: 创建配置
- `GET /admin/v1/system-settings`: 列出配置
- `GET /admin/v1/system-settings/{id}`: 获取配置详情
- `PUT /admin/v1/system-settings/{id}`: 更新配置
- `DELETE /admin/v1/system-settings/{id}`: 删除配置

所有端点 SHALL 要求管理员认证。

#### Scenario: 管理员创建配置

- **WHEN** 管理员发送 POST /admin/v1/system-settings，body 包含 name、code 和 attributes
- **THEN** 创建成功返回 201，响应包含完整的配置和属性值

#### Scenario: 管理员列出配置

- **WHEN** 管理员发送 GET /admin/v1/system-settings
- **THEN** 返回当前租户的所有配置列表

#### Scenario: 未认证用户访问管理端点

- **WHEN** 未认证用户发送 GET /admin/v1/system-settings
- **THEN** 返回 401 未认证错误

### Requirement: Console API 端点

iam/controllers/console/system_setting_controller.py SHALL 提供用户端 API：
- `GET /console/v1/system-settings`: 列出本租户配置
- `GET /console/v1/system-settings/{id}`: 获取配置详情
- `GET /console/v1/system-settings/by-code/{code}`: 按编号获取配置

Console 端点 SHALL 只允许读取操作（不可创建/更新/删除）。

#### Scenario: 用户按编号查询配置

- **WHEN** 用户发送 GET /console/v1/system-settings/by-code/SMTP
- **THEN** 返回本租户 code 为 "SMTP" 的配置详情和属性值列表

#### Scenario: 用户尝试创建配置

- **WHEN** 用户发送 POST /console/v1/system-settings
- **THEN** 返回 405 方法不允许

### Requirement: Pydantic Schema 定义请求和响应 DTO

iam/schemas/ SHALL 定义以下 Pydantic 模型：

**SystemSettingAttributeCreate**:
- name: str (required, max_length=256)
- display_name: str | None
- description: str | None
- data_type: AttributeDataType = STRING
- value: str | None
- ext_data: dict | None
- can_edit: bool = True
- is_require: bool = False
- index: int = 0

**SystemSettingCreate**:
- code: str (required, max_length=20)
- name: str (required, max_length=256)
- display_name: str | None
- description: str | None
- application_id: str | None
- application_name: str | None
- can_edit: bool = True
- is_require: bool = False
- index: int = 0
- attributes: list[SystemSettingAttributeCreate] = []

**SystemSettingUpdate**: 同 SystemSettingCreate 但所有字段可选

**SystemSettingAttributeResponse**: 含 id、setting_id 和所有字段，from_attributes=True

**SystemSettingResponse**: 含 id、tenant_id、code 和所有字段 + attributes 列表，from_attributes=True

#### Scenario: Schema 校验必填字段

- **WHEN** 提交 SystemSettingCreate 时缺少 code 或 name
- **THEN** Pydantic 校验失败，返回字段缺失错误

#### Scenario: Schema 校验 code 长度

- **WHEN** 提交 SystemSettingCreate 时 code 长度超过 20
- **THEN** Pydantic 校验失败，返回长度超限错误

### Requirement: Alembic 迁移创建数据库表

iam/migrations/ SHALL 包含 Alembic 迁移文件，创建 `system_settings` 和 `system_setting_attributes` 两张表及其约束和索引。

#### Scenario: 执行迁移后表结构正确

- **WHEN** 执行 Alembic 迁移 `uv run python manage.py db migrate`
- **THEN** system_settings 和 system_setting_attributes 表创建成功，所有约束和索引正确