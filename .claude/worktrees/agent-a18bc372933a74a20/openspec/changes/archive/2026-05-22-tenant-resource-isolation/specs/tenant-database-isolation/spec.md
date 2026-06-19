## ADDED Requirements

### Requirement: 独立数据库物理隔离

系统 SHALL 支持租户使用独立的数据库实例，实现数据物理隔离。

#### Scenario: 租户使用独立数据库
- **WHEN** 租户配置了独立数据库（db_name 不为空）
- **THEN** 租户数据存储在独立数据库中
- **AND** 数据完全物理隔离，无法被其他租户访问

#### Scenario: 独立数据库无需 tenant_id 过滤
- **WHEN** 租户使用独立数据库
- **THEN** 查询时无需添加 tenant_id 过滤条件
- **AND** 数据天然隔离

### Requirement: 数据库模式选择

系统 SHALL 支持逻辑隔离和物理隔离两种模式。

#### Scenario: 逻辑隔离模式
- **WHEN** 租户未配置独立数据库
- **THEN** 使用共享数据库 + tenant_id 字段过滤
- **AND** 自动添加 WHERE tenant_id = :current_tenant_id 条件

#### Scenario: 物理隔离模式
- **WHEN** 租户配置了独立数据库
- **THEN** 使用独立数据库连接
- **AND** 不添加 tenant_id 过滤条件

### Requirement: 平滑迁移支持

系统 SHALL 支持租户从逻辑隔离迁移到物理隔离。

#### Scenario: 迁移前数据导出
- **WHEN** 租户从共享数据库迁移到独立数据库
- **THEN** 系统提供数据导出功能

#### Scenario: 迁移后数据导入
- **WHEN** 租户数据导入到独立数据库
- **THEN** 系统提供数据导入功能
