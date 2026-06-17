## 新增需求

### 需求: 租户详情聚合响应 Schema

系统 SHALL 提供 `TenantDetailResponse` 聚合响应 Schema，包含租户基础信息和资源配置引用。

#### 场景: Schema 字段完整性
- **当** 构建 `TenantDetailResponse` 时
- **那么** 必须包含以下字段：id、name、code、status、contact_name、contact_email、contact_phone、expired_at、settings、db_config、storage_config、cache_config、queue_config、pubsub_config、created_at、updated_at

#### 场景: 资源配置引用可为空
- **当** 租户未绑定某类资源配置时
- **那么** 对应的配置引用字段为 None

### 需求: from_tenant() 转换方法

`TenantDetailResponse` SHALL 提供 `from_tenant()` 类方法，支持从 Tenant 实体和资源配置引用构建响应对象。

#### 场景: 成功转换
- **当** 调用 `TenantDetailResponse.from_tenant(tenant, db_ref, storage_ref, cache_ref, queue_ref, pubsub_ref)`
- **那么** 返回完整的 `TenantDetailResponse` 对象

#### 场景: 部分资源配置为空
- **当** 某些资源配置引用为 None 时
- **那么** 对应字段正确设置为 None

### 需求: 资源配置引用 Schema

系统 SHALL 提供 `ResourceConfigReferenceResponse` Schema，用于表示资源配置的简要信息（id 和 name）。

#### 场景: Schema 字段
- **当** 构建 `ResourceConfigReferenceResponse` 时
- **那么** 必须包含 id 和 name 字段

## 修改需求

无

## 移除需求

无
