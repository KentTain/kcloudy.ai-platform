## ADDED Requirements

### Requirement: 任务消息携带租户信息

系统 SHALL 在任务入队时自动记录 tenant_id。

#### Scenario: 任务入队自动携带租户 ID
- **WHEN** 在租户上下文为 `tenant_001` 时入队任务
- **THEN** 任务消息自动包含 `tenant_id: "tenant_001"`

#### Scenario: 无租户上下文时入队
- **WHEN** 在无租户上下文时入队任务
- **THEN** 任务消息的 `tenant_id` 字段为 `None`

### Requirement: 任务执行时恢复租户上下文

系统 SHALL 在任务执行时自动恢复租户上下文。

#### Scenario: 任务执行恢复租户上下文
- **WHEN** 任务消息包含 `tenant_id: "tenant_001"`
- **THEN** 执行前加载租户信息并设置租户上下文
- **AND** 执行完成后清理租户上下文

#### Scenario: 任务执行时租户不存在
- **WHEN** 任务消息包含 `tenant_id` 但租户不存在
- **THEN** 记录警告日志，任务继续执行（无租户上下文）

#### Scenario: 任务执行无租户信息
- **WHEN** 任务消息不包含 `tenant_id`
- **THEN** 任务正常执行（无租户上下文）

### Requirement: 任务执行异常处理

系统 SHALL 确保任务异常时上下文被清理。

#### Scenario: 任务异常后上下文清理
- **WHEN** 任务执行过程中发生异常
- **THEN** 租户上下文仍被清理

### Requirement: 任务消息格式

系统 SHALL 定义标准的任务消息格式。

#### Scenario: 任务消息结构
- **WHEN** 创建任务消息
- **THEN** 消息包含以下字段：
  - `task_id`: 任务唯一标识
  - `task_type`: 任务类型
  - `payload`: 任务负载数据
  - `tenant_id`: 租户 ID（自动填充）
  - `created_at`: 创建时间
