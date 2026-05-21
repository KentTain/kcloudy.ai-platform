## Why

当前项目的消息监听器（`application_listener.py`）和任务调度器（`application_task.py`）均为占位符，仅打印"尚未实现"。参考 Alon 项目的 listeners/tasks 架构，需要在 demo 模块中实现最小可用的示例 listeners 和 tasks，使项目的消息处理和定时调度能力可用，并为后续业务扩展提供可参考的实现模式。

## What Changes

- 实现 demo 模块的 listeners 子模块，包含：
  - Pub/Sub 示例处理器：监听主题消息并处理（如心跳通知）
  - Queue 示例处理器：消费队列消息并执行任务（如数据集处理通知）
  - `setup_listeners()` / `cleanup_listeners()` 生命周期管理
  - 替换 `application_listener.py` 占位符为真实实现
- 实现 demo 模块的 tasks 子模块，包含：
  - 本地定时任务示例：周期性执行的简单任务（如日志心跳）
  - 集群定时任务示例：跨实例唯一执行的定时任务（如队列状态检查）
  - `setup_scheduler()` / `cleanup_scheduler()` 生命周期管理
  - 替换 `application_task.py` 占位符为真实实现
- 为 listeners 和 tasks 编写单元测试和集成测试

## Capabilities

### New Capabilities

- `demo-listeners`: demo 模块的消息监听器能力——基于 framework 的 PubSub/Queue handler 基类实现示例处理器，包含 setup/cleanup 生命周期管理
- `demo-tasks`: demo 模块的定时任务调度能力——基于 APScheduler 实现本地/集群双调度器，包含示例任务和 setup/cleanup 生命周期管理

### Modified Capabilities


## Impact

- **代码变更**：`src/demo/application_listener.py`、`src/demo/application_task.py` 从占位符替换为真实实现
- **新增文件**：`src/demo/listeners/`、`src/demo/tasks/` 子包
- **新增依赖**：`apscheduler`（如果尚未引入）
- **测试变更**：新增 `tests/demo/unit/listeners/`、`tests/demo/unit/tasks/`、`tests/demo/integration/listeners/`、`tests/demo/integration/tasks/` 目录
- **API 端点**：无新增或变更，listeners/tasks 为后台服务
- **数据库**：无变更
