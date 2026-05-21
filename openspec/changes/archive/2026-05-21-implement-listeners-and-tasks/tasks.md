## 1. 项目基础设施

- [x] 1.1 添加 `apscheduler` 依赖到 `pyproject.toml`
- [x] 1.2 创建 `src/demo/listeners/` 子包目录结构（`__init__.py`、`services/pubsub/`、`services/queue/`）
- [x] 1.3 创建 `src/demo/tasks/` 子包目录结构（`__init__.py`、`services/`）

## 2. Listeners 常量与处理器

- [x] 2.1 创建 `src/demo/listeners/services/pubsub/constants.py`，定义 `HEARTBEAT_TOPIC = "demo:heartbeat"`
- [x] 2.2 创建 `src/demo/listeners/services/queue/constants.py`，定义 `DATASET_NOTIFY_QUEUE = "demo:dataset:notify"`
- [x] 2.3 实现 `src/demo/listeners/services/pubsub/heartbeat_handler.py`，`HeartbeatHandler(SingleTopicHandler)` 监听 `HEARTBEAT_TOPIC`，记录日志
- [x] 2.4 实现 `src/demo/listeners/services/queue/dataset_notify_handler.py`，`DatasetNotifyHandler(SingleQueueHandler)` 消费 `DATASET_NOTIFY_QUEUE`，记录日志

## 3. Listeners 生命周期与入口

- [x] 3.1 实现 `src/demo/listeners/setup.py`，包含 `setup_listeners()` 和 `cleanup_listeners()`
- [x] 3.2 替换 `src/demo/application_listener.py` 占位符，实现真实启动逻辑（调用 `setup_listeners()`，持续运行直到信号终止）

## 4. Tasks 服务

- [x] 4.1 实现 `src/demo/tasks/services/heartbeat_task.py`，`heartbeat_task()` 异步函数，每 60 秒记录时间戳日志
- [x] 4.2 实现 `src/demo/tasks/services/queue_status_task.py`，`queue_status_task()` 异步函数，检查 `DATASET_NOTIFY_QUEUE` 队列长度并记录日志

## 5. Tasks 生命周期与入口

- [x] 5.1 实现 `src/demo/tasks/setup.py`，包含双调度器创建、任务注册、`setup_scheduler()` 和 `cleanup_scheduler()`
- [x] 5.2 替换 `src/demo/application_task.py` 占位符，实现真实启动逻辑（调用 `setup_scheduler()`，持续运行直到信号终止）

## 6. 单元测试

- [x] 6.1 创建 `tests/demo/unit/listeners/test_heartbeat_handler.py`，测试 `HeartbeatHandler` 的 `handle()` 方法
- [x] 6.2 创建 `tests/demo/unit/listeners/test_dataset_notify_handler.py`，测试 `DatasetNotifyHandler` 的 `handle()` 方法
- [x] 6.3 创建 `tests/demo/unit/tasks/test_heartbeat_task.py`，测试 `heartbeat_task()` 正常执行和异常处理
- [x] 6.4 创建 `tests/demo/unit/tasks/test_queue_status_task.py`，测试 `queue_status_task()` 正常执行和 QueueProvider 不可用场景
- [x] 6.5 创建 `tests/demo/unit/tasks/test_scheduler_setup.py`，测试 `setup_scheduler()` 和 `cleanup_scheduler()` 生命周期

## 7. 集成测试

- [x] 7.1 创建 `tests/demo/integration/listeners/test_pubsub_integration.py`，测试 Pub/Sub 处理器与 Redis 的真实交互
- [x] 7.2 创建 `tests/demo/integration/listeners/test_queue_integration.py`，测试 Queue 处理器与 Redis 的真实交互
- [x] 7.3 创建 `tests/demo/integration/tasks/test_scheduler_integration.py`，测试双调度器与 Redis 的真实交互

## 8. 验证

- [x] 8.1 运行全部单元测试，确保通过
- [x] 8.2 运行全部集成测试（需 Redis），确保通过
- [x] 8.3 执行 `python manage.py runlistener` 验证监听器启动
- [x] 8.4 执行 `python manage.py runtask` 验证调度器启动
