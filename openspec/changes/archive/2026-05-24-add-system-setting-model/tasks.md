## 1. Framework 层：PropertyMixin + PropertyAttributeMixin + AttributeDataType + PropertyUtil

- [x] 1.1 创建 `framework/database/mixins/property.py`，实现 PropertyMixin（属性容器字段：name, display_name, description, can_edit, is_require, index）
- [x] 1.2 在同一文件实现 PropertyAttributeMixin（属性值字段：data_type, name, display_name, description, value, ext_data, can_edit, is_require, index），其中 value 为 Text、ext_data 为 JSONB
- [x] 1.3 在同一文件实现 AttributeDataType(str, Enum) 枚举（string, integer, decimal, date_time, boolean, json）
- [x] 1.4 创建 `framework/utils/property_util.py`，实现 PropertyUtil 静态工具类（get_attribute_by_name, get_value_by_name, get_values_by_name, get_typed_value, coerce_value）
- [x] 1.5 更新 `framework/database/__init__.py`，导出 PropertyMixin、PropertyAttributeMixin、AttributeDataType
- [x] 1.6 编写 framework 单元测试：PropertyUtil.coerce_value 各类型转换、边界条件、异常场景

## 2. IAM 层：SystemSetting + SystemSettingAttribute 模型

- [x] 2.1 创建 `iam/models/system_setting.py`，实现 SystemSetting 模型（BaseModel + TenantMixin + PropertyMixin + ActiveRecordMixin），表名 system_settings，独有字段 code/application_id/application_name，relationship attributes 指向 SystemSettingAttribute
- [x] 2.2 创建 `iam/models/system_setting_attribute.py`，实现 SystemSettingAttribute 模型（BaseModel + TenantMixin + PropertyAttributeMixin），表名 system_setting_attributes，独有字段 setting_id（FK + CASCADE），relationship setting back_populates attributes
- [x] 2.3 定义数据库约束：uq_system_settings_tenant_code (tenant_id, code)、uq_system_setting_attributes_setting_name (setting_id, name)、相关索引
- [x] 2.4 更新 `iam/models/__init__.py`，导出 SystemSetting、SystemSettingAttribute

## 3. IAM 层：Pydantic Schema

- [x] 3.1 创建 `iam/schemas/admin/system_setting.py`，实现 SystemSettingAttributeCreate、SystemSettingCreate、SystemSettingUpdate、SystemSettingAttributeResponse、SystemSettingResponse
- [x] 3.2 创建 `iam/schemas/console/system_setting.py`，实现 console 端只读响应 Schema（SystemSettingListResponse、SystemSettingDetailResponse）

## 4. IAM 层：Service

- [x] 4.1 创建 `iam/services/system_setting_service.py`，实现 SystemSettingService（create_setting, get_setting, update_setting, delete_setting, list_settings, get_setting_by_code）
- [x] 4.2 update_setting 方法需支持属性值同步更新（已有属性更新、新增属性创建、多余属性删除）

## 5. IAM 层：Controller + 路由注册

- [x] 5.1 创建 `iam/controllers/admin/system_setting_controller.py`，实现 admin 端 CRUD 端点（POST/GET/PUT/DELETE /admin/v1/system-settings）
- [x] 5.2 创建 `iam/controllers/console/system_setting_controller.py`，实现 console 端只读端点（GET /console/v1/system-settings、GET /console/v1/system-settings/by-code/{code}）
- [x] 5.3 在路由注册入口（application_web.py 或模块路由文件）注册 SystemSetting 路由

## 6. 数据库迁移

- [x] 6.1 创建 Alembic 迁移文件，建 system_settings 和 system_setting_attributes 表及其约束和索引

## 7. 测试

- [x] 7.1 编写 SystemSetting Service 单元测试（CRUD、属性值同步更新、租户隔离、唯一约束）
- [x] 7.2 编写 SystemSetting Controller API 集成测试（admin CRUD、console 只读、认证、租户上下文）