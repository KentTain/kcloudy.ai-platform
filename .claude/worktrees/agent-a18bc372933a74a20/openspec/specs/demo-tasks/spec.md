# Demo Tasks 规范

## Purpose

Demo 模块的定时任务调度能力——基于 APScheduler 实现本地/集群双调度器，包含示例任务和 setup/cleanup 生命周期管理。

## Requirements

### Requirement: 本地心跳定时任务
系统 SHALL 提供 `heartbeat_task()` 异步函数，作为本地定时任务，每 60 秒记录一条包含当前时间戳的日志。

#### Scenario: 心跳任务执行
- **WHEN** 心跳任务被调度器触发
- **THEN** 记录包含当前 UTC 时间戳的日志消息

#### Scenario: 心跳任务异常
- **WHEN** 心跳任务执行过程中抛出异常
- **THEN** 异常被捕获并记录错误日志，不影响后续调度

### Requirement: 集群队列状态检查任务
系统 SHALL 提供 `queue_status_task()` 异步函数，作为集群定时任务，每 5 分钟检查 `demo:dataset:notify` 队列长度并记录日志。

#### Scenario: 队列有消息
- **WHEN** 队列状态检查任务执行且队列中有待处理消息
- **THEN** 记录包含队列名称和当前消息数的日志

#### Scenario: 队列为空
- **WHEN** 队列状态检查任务执行且队列为空
- **THEN** 记录队列为空的日志

#### Scenario: QueueProvider 不可用
- **WHEN** 队列状态检查任务执行但 QueueProvider 不可用
- **THEN** 异常被捕获并记录错误日志，不影响后续调度

### Requirement: 双调度器架构
系统 SHALL 使用两个独立的 `AsyncIOScheduler` 实例：本地调度器（MemoryJobStore）和集群调度器（RedisJobStore），分别管理本地任务和集群任务。

#### Scenario: 启动调度器
- **WHEN** 调用 `setup_scheduler()`
- **THEN** 本地任务注册到本地调度器，集群任务注册到集群调度器，有任务的调度器自动启动

#### Scenario: 清理调度器
- **WHEN** 调用 `cleanup_scheduler()`
- **THEN** 所有运行中的调度器优雅停止（wait=True）

#### Scenario: 仅启动本地调度器
- **WHEN** 集群任务未注册（如 Redis 不可用）
- **THEN** 仅本地调度器启动，集群调度器不启动

### Requirement: 任务注册声明式配置
系统 SHALL 使用声明式元组列表注册任务，而非命令式逐个添加。本地任务使用 3-元组 `(func, task_id, trigger_args)`，集群任务使用 4-元组 `(func, task_id, trigger, trigger_args)`。

#### Scenario: 本地任务注册格式
- **WHEN** 定义本地任务列表
- **THEN** 每个任务为 `(func, "task_id", {"seconds": 60})` 格式

#### Scenario: 集群任务注册格式
- **WHEN** 定义集群任务列表
- **THEN** 每个任务为 `(func, "task_id", "interval", {"minutes": 5})` 格式

### Requirement: application_task.py 入口
系统 SHALL 将 `application_task.py` 从占位符替换为真实实现，通过 `manage.py runtask` 命令启动调度器。

#### Scenario: 运行调度器命令
- **WHEN** 执行 `python manage.py runtask`
- **THEN** 调用 `setup_scheduler()` 启动定时调度，进程持续运行直到被终止
