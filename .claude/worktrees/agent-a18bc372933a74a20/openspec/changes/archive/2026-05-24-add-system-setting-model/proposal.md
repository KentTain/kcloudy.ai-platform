## Why

当前项目的租户配置（`TenantConfig`）采用扁平键值模型，缺少属性分组、类型元数据和结构化扩展能力。需要借鉴已有 .NET/Java 技术栈的 PropertyBase/PropertyAttributeBase EAV 模式，实现通用配置模型，支持每个租户下结构化的系统配置管理。

## What Changes

- 新增 `PropertyMixin`（属性容器通用字段）和 `PropertyAttributeMixin`（属性值通用字段）到 framework/database/mixins/property.py
- 新增 `AttributeDataType` 枚举（string, integer, decimal, date_time, boolean, json）到 framework/database/mixins/property.py，使用 `str, Enum`
- 新增 `PropertyUtil` 工具类到 framework/utils/property_util.py，提供属性取值、提取和类型转换方法
- 新增 `SystemSetting` 模型（继承 BaseModel + TenantMixin + PropertyMixin + ActiveRecordMixin）到 iam/models/system_setting.py
- 新增 `SystemSettingAttribute` 模型（继承 BaseModel + TenantMixin + PropertyAttributeMixin）到 iam/models/system_setting_attribute.py
- 新增 SystemSetting 与 SystemSettingAttribute 的 1:N relationship
- 新增 Pydantic Schema（Create/Update/Response DTO）到 iam/schemas/
- 新增 SystemSettingService 业务逻辑到 iam/services/
- 新增 SystemSettingController（admin/console）到 iam/controllers/
- 新增 Alembic 迁移文件
- 更新 framework/database/__init__.py 导出 PropertyMixin、PropertyAttributeMixin、AttributeDataType
- 更新 iam/models/__init__.py 导出新模型

## Capabilities

### New Capabilities

- `property-mixin`: framework 层的属性配置模式抽象（PropertyMixin + PropertyAttributeMixin + AttributeDataType + PropertyUtil）
- `system-setting`: IAM 模块的租户级系统配置实体（SystemSetting + SystemSettingAttribute + Service + Controller + Schema）

### Modified Capabilities

- `database`: 新增 PropertyMixin、PropertyAttributeMixin、AttributeDataType 导出

## Impact

- **数据库**：新增 `system_settings` 和 `system_setting_attributes` 两张表，需要 Alembic 迁移
- **framework**：新增 property.py mixin 和 property_util.py 工具类，扩展 database 模块导出
- **iam**：新增模型、Service、Controller、Schema，扩展模块导出
- **API**：新增 `/admin/v1/system-settings` 和 `/console/v1/system-settings` 端点
- **租户隔离**：SystemSetting 和 SystemSettingAttribute 都使用 TenantMixin，TenantQueryInterceptor 自动过滤，TenantEventListener 自动注入 tenant_id
- **兼容性**：不影响现有 TenantConfig 模型，两者并存，SystemSetting 是更结构化的配置方案