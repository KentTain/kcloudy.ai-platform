# demo-tenant-isolation Specification

## Purpose
TBD - created by archiving change complete-iam-multi-tenancy. Update Purpose after archive.
## Requirements
### Requirement: Dataset 模型支持租户隔离

系统 SHALL 在 Dataset 模型中添加租户关联字段，确保数据按租户隔离。

#### Scenario: Dataset 模型包含 tenant_id
- **GIVEN** Dataset 模型已添加 TenantMixin
- **WHEN** 查询数据集
- **THEN** 每个 Dataset 记录包含 tenant_id 字段
- **AND** 自动过滤只看当前租户的数据

#### Scenario: 创建数据集时自动关联租户
- **GIVEN** 当前请求上下文已设置租户 ID = "tenant-123"
- **WHEN** 用户 POST /api/v1/datasets 创建数据集
- **THEN** 创建的数据集自动关联 tenant_id = "tenant-123"
- **AND** 用户无法创建属于其他租户的数据集

#### Scenario: 跨租户数据隔离
- **GIVEN** 用户 A 属于租户 "tenant-A"，用户 B 属于租户 "tenant-B"
- **AND** 两个租户都存在名为 "Test Dataset" 的数据集
- **WHEN** 用户 A 查询数据集列表
- **THEN** 只返回租户 "tenant-A" 的数据集
- **AND** 不会返回租户 "tenant-B" 的数据集

---

### Requirement: Dataset Service 层租户过滤

系统 SHALL 在 Service 层实现租户数据过滤逻辑。

#### Scenario: 查询数据集时自动注入 tenant_id 过滤
- **GIVEN** 当前租户上下文为 tenant_id = "tenant-123"
- **WHEN** 调用 DatasetService.list() 查询数据集
- **THEN** SQL 查询自动添加 WHERE tenant_id = 'tenant-123' 条件

#### Scenario: 更新数据集时验证租户归属
- **GIVEN** 当前租户上下文为 tenant_id = "tenant-123"
- **AND** 数据集 A 属于 tenant-A，数据集 B 属于 tenant-B
- **WHEN** 用户尝试更新数据集 B
- **THEN** 系统返回 HTTP 403 错误，消息为 "无权访问该数据集"

#### Scenario: 删除数据集时验证租户归属
- **GIVEN** 当前租户上下文为 tenant_id = "tenant-123"
- **AND** 数据集 A 属于 tenant-123，数据集 B 属于 tenant-B
- **WHEN** 用户尝试删除数据集 B
- **THEN** 系统返回 HTTP 403 错误，消息为 "无权操作"

---

### Requirement: Controller 层获取当前租户

系统 SHALL 在 Controller 层提供获取当前租户信息的能力。

#### Scenario: 从 TenantContext 获取租户 ID
- **GIVEN** 请求已通过 TenantMiddleware 设置租户上下文
- **WHEN** 在 Controller 中调用 get_tenant_id()
- **THEN** 返回当前租户的 ID

#### Scenario: 未设置租户时返回错误
- **GIVEN** 请求未通过 TenantMiddleware（跳过了租户验证）
- **WHEN** 在 Controller 中调用 get_tenant_id()
- **THEN** 返回 None，Controller 应返回 HTTP 400 错误

---

### Requirement: Demo 模块租户感知配置

系统 SHALL 提供配置开关，控制 Demo 模块是否启用租户隔离。

#### Scenario: 启用租户隔离
- **GIVEN** 配置文件中 tenant.isolation.enabled = true
- **WHEN** DatasetService 处理请求
- **THEN** 自动应用租户过滤

#### Scenario: 禁用租户隔离（开发模式）
- **GIVEN** 配置文件中 tenant.isolation.enabled = false
- **WHEN** DatasetService 处理请求
- **THEN** 不应用租户过滤，返回所有数据（仅管理员可用）

