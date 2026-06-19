## Context

当前 demo 模块的 `application_listener.py` 和 `application_task.py` 均为占位符实现，仅打印"尚未实现"后退出。framework 层已提供完整的消息基础设施（`QueueProvider`、`PubSubProvider`、`QueueMessageHandler`、`TopicMessageHandler` 等基类及 Redis 实现），但 demo 层尚未接入。

参考 Alon 项目的 listeners/tasks 架构：
- **Listeners**：双模式（Pub/Sub 广播 + Queue 竞争消费），通过 `setup_listeners()` / `cleanup_listeners()` 管理生命周期
- **Tasks**：双调度器（本地 MemoryJobStore + 集群 RedisJobStore），通过 `setup_scheduler()` / `cleanup_scheduler()` 管理生命周期

## Goals / Non-Goals

**Goals:**

- 实现最小可用的 listeners 子模块，包含一个 Pub/Sub 示例处理器和一个 Queue 示例处理器
- 实现最小可用的 tasks 子模块，包含一个本地定时任务和一个集群定时任务
- 替换 `application_listener.py` 和 `application_task.py` 的占位符实现
- 编写单元测试和集成测试验证功能正确性
- 遵循 Alon 项目的架构模式，保持代码风格一致

**Non-Goals:**

- 不实现复杂的业务逻辑（如文档处理、向量计算等）
- 不实现跨节点任务取消机制（Alon 的 `ACTIVE_ASYNCIO_TASKS` 全局注册表）
- 不实现扩展系统（extension listeners/tasks 注册）
- 不修改 framework 层的任何代码

## Decisions

### 1. Listeners 子模块结构

**决策**：采用 Alon 的 `services/pubsub/` + `services/queue/` 分层结构，在 `src/demo/listeners/` 下组织。

```
src/demo/listeners/
├── __init__.py
├── setup.py                          # setup_listeners() / cleanup_listeners()
├── services/
│   ├── __init__.py
│   ├── pubsub/
│   │   ├── __init__.py
│   │   ├── constants.py              # 主题常量
│   │   └── heartbeat_handler.py      # 心跳消息处理器
│   └── queue/
│       ├── __init__.py
│       ├── constants.py              # 队列常量
│       └── dataset_notify_handler.py # 数据集通知处理器
```

**理由**：与 Alon 保持一致的结构，Pub/Sub 和 Queue 分离，便于理解和扩展。

### 2. Tasks 子模块结构

**决策**：采用 Alon 的双调度器模式，在 `src/demo/tasks/` 下组织。

```
src/demo/tasks/
├── __init__.py
├── setup.py                          # setup_scheduler() / cleanup_scheduler()
└── services/
    ├── __init__.py
    ├── heartbeat_task.py             # 本地心跳任务
    └── queue_status_task.py          # 集群队列状态检查任务
```

**理由**：双调度器模式已在 Alon 中验证，本地任务适合日志心跳等每实例运行场景，集群任务适合队列状态检查等需唯一执行场景。

### 3. 示例 Pub/Sub 处理器：心跳消息

**决策**：实现 `HeartbeatHandler(SingleTopicHandler)`，监听 `demo:heartbeat` 主题，收到消息后记录日志。

**理由**：最简单的 Pub/Sub 示例，不依赖外部服务，便于测试验证。

### 4. 示例 Queue 处理器：数据集通知

**决策**：实现 `DatasetNotifyHandler(SingleQueueHandler)`，消费 `demo:dataset:notify` 队列，收到消息后记录日志并可选更新数据集状态。

**理由**：与现有 `Dataset` 模型关联，展示 Queue 处理器如何与业务 Model 交互，同时保持简单。

### 5. 示例本地任务：心跳日志

**决策**：实现 `heartbeat_task()` 异步函数，每 60 秒记录一条包含当前时间戳的日志。

**理由**：对应 Alon 的 `my_task`，最简单的定时任务示例。

### 6. 示例集群任务：队列状态检查

**决策**：实现 `queue_status_task()` 异步函数，每 5 分钟检查队列长度并记录日志。

**理由**：展示集群任务如何使用 framework 的 `QueueProvider` 获取队列信息，同时保持简单。

### 7. 调度器依赖选择

**决策**：使用 APScheduler 4.x（如果兼容）或 3.x，与 Alon 一致使用 `AsyncIOScheduler`。

**理由**：APScheduler 是 Python 生态最成熟的异步调度库，Alon 已验证其可行性。

### 8. application_listener.py 入口实现

**决策**：在 `lifespan` 上下文管理器中调用 `setup_listeners()` 启动监听，退出时调用 `cleanup_listeners()` 清理。

**理由**：与 Alon 的应用启动模式一致，manage.py 的 `runlistener` 命令触发此流程。

### 9. application_task.py 入口实现

**决策**：在 `lifespan` 上下文管理器中调用 `setup_scheduler()` 启动调度器，退出时调用 `cleanup_scheduler()` 清理。

**理由**：同上，manage.py 的 `runtask` 命令触发此流程。

## Risks / Trade-offs

- **[APScheduler 版本]** APScheduler 4.x API 与 3.x 不兼容 → 优先使用 3.x（与 Alon 一致），确保稳定性
- **[Redis 依赖]** 集群调度器和消息处理器依赖 Redis → 集成测试需 Redis 可用，单元测试通过 mock 隔离
- **[最小化实现]** 示例处理器逻辑简单，可能不足以展示完整模式 → 在代码注释中说明扩展方向
