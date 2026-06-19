# Spec: 模块 Schema 隔离

## Purpose

为每个业务模块提供独立的 PostgreSQL schema，实现数据库层面的模块隔离。

## Requirements

### Requirement: 模块拥有独立的 PostgreSQL schema

系统 SHALL 为每个业务模块分配独立的 PostgreSQL schema，模块内的所有数据库表自动归属该 schema。

#### Scenario: 模块表自动归属对应 schema

- **WHEN** 定义模块 `iam` 的数据模型并继承 `iam.models.BaseModel`
- **THEN** 该模型对应的数据库表 `users` 自动创建在 `iam` schema 下（`iam.users`）

#### Scenario: 多模块表空间隔离

- **GIVEN** 系统存在 `iam` 和 `demo` 两个模块
- **WHEN** 执行数据库迁移
- **THEN** `iam` 模块的表在 `iam` schema
- **AND** `demo` 模块的表在 `demo` schema
- **AND** 两模块的同名表不会冲突

### Requirement: 模块独立管理迁移版本

系统 SHALL 为每个模块提供独立的 Alembic 版本表，支持模块级迁移控制。

#### Scenario: 模块独立版本表

- **GIVEN** `iam` 模块配置 `version_table_schema="iam"`
- **WHEN** 执行 `iam` 模块的数据库迁移
- **THEN** 迁移版本记录存储在 `iam.alembic_version` 表
- **AND** 不影响其他模块的迁移状态

#### Scenario: 模块迁移独立执行

- **GIVEN** `iam` 模块已有迁移版本 `abc123`
- **AND** `demo` 模块已有迁移版本 `def456`
- **WHEN** 执行 `python manage.py db migrate --module iam`
- **THEN** 仅 `iam` 模块应用新迁移
- **AND** `demo` 模块的迁移状态不受影响

### Requirement: 跨模块数据引用无外键约束

系统 SHALL 移除跨模块的外键约束，改用应用层一致性检查。

#### Scenario: 租户 ID 字段无外键

- **GIVEN** `demo.models.Dataset` 使用 `TenantMixin`
- **WHEN** `TenantMixin` 定义 `tenant_id: Mapped[str]` 字段
- **THEN** 该字段为普通字符串类型
- **AND** 不存在指向 `iam.tenants.id` 的外键约束

#### Scenario: 应用层校验租户存在性

- **WHEN** 创建 `Dataset` 记录时指定 `tenant_id`
- **THEN** 系统在应用层校验该租户是否存在于 `iam.tenants` 表
- **AND** 若租户不存在则抛出业务异常

### Requirement: 模块 schema 创建与销毁

系统 SHALL 提供脚本支持模块 schema 的创建与销毁。

#### Scenario: 重建模块 schema

- **GIVEN** 需要重建 `iam` 模块的数据库结构
- **WHEN** 执行 `python manage.py db rebuild --module iam`
- **THEN** 系统执行 `DROP SCHEMA IF EXISTS iam CASCADE`
- **AND** 执行 `CREATE SCHEMA iam`
- **AND** 执行 `alembic upgrade head` 应用迁移
- **AND** 执行 seed 初始化数据

#### Scenario: 重建所有模块

- **WHEN** 执行 `python manage.py db rebuild --all`
- **THEN** 系统对所有已注册模块依次执行重建流程
