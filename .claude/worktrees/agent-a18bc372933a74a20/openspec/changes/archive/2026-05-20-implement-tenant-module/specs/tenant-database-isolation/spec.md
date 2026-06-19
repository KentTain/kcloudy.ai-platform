## ADDED Requirements

### Requirement: 模型租户字段混入

系统 SHALL 提供 TenantMixin，为模型自动添加 tenant_id 字段和索引。

#### Scenario: 继承 TenantMixin
- **WHEN** 模型继承 TenantMixin
- **THEN** 模型自动拥有 `tenant_id` 字段（VARCHAR(32)，非空）
- **AND** 自动创建 `tenant_id` 索引

### Requirement: 自动填充 tenant_id

系统 SHALL 在插入数据时自动填充 tenant_id。

#### Scenario: 插入数据自动填充 tenant_id
- **WHEN** 创建新记录且未指定 tenant_id
- **THEN** 自动从 `TenantContext` 获取当前租户 ID 并填充

#### Scenario: 管理员场景跳过自动填充
- **WHEN** 设置 `skip_tenant=True` 标志
- **THEN** 不自动填充 tenant_id

### Requirement: 查询自动过滤 tenant_id

系统 SHALL 在查询时自动添加 tenant_id 过滤条件。

#### Scenario: 查询自动过滤
- **WHEN** 执行查询操作
- **THEN** 自动添加 `WHERE tenant_id = :current_tenant_id` 条件

#### Scenario: 管理员场景跳过自动过滤
- **WHEN** 设置 `skip_tenant=True` 标志
- **THEN** 不添加 tenant_id 过滤条件

### Requirement: 更新和删除隔离

系统 SHALL 在更新和删除操作中自动应用租户过滤。

#### Scenario: 更新自动过滤
- **WHEN** 执行更新操作
- **THEN** 自动添加 `WHERE tenant_id = :current_tenant_id` 条件

#### Scenario: 删除自动过滤
- **WHEN** 执行删除操作
- **THEN** 自动添加 `WHERE tenant_id = :current_tenant_id` 条件

### Requirement: 跨租户数据隔离

系统 SHALL 确保不同租户的数据相互隔离。

#### Scenario: 查询不到其他租户数据
- **WHEN** 租户 A 查询数据
- **THEN** 只能查询到 tenant_id = 租户 A ID 的数据

#### Scenario: 无法更新其他租户数据
- **WHEN** 租户 A 尝试更新租户 B 的数据
- **THEN** 更新影响行数为 0

#### Scenario: 无法删除其他租户数据
- **WHEN** 租户 A 尝试删除租户 B 的数据
- **THEN** 删除影响行数为 0
