# Memory Task 模块

后台任务管控服务，支持任务停止、超时清理、跨进程通信。

## 文件

| 文件 | 职责 |
|------|------|
| constants.py | ACTIVE_ASYNCIO_TASKS / ACTIVE_CLEANUP_TASKS 字典、TASK_TYPE_GENERATE_LLM 常量 |
| cancel_asyncio_task.py | CancelAsyncioTaskHandler：订阅 PubSub 取消信号，取消本地 asyncio 任务，更新消息状态 |
| helpers.py | stop_task_by_id（本地取消 + 广播）、cleanup_task_resources（资源清理）、stop_message_by_id（更新消息状态） |
| cleanup.py | cleanup_task_after_timeout：超时后发布取消信号并清理任务 |

## 任务停止流程

1. `stop_task_by_id()` 先在本地查找任务并取消
2. 本地未找到则通过 PubSub 广播取消请求
3. `CancelAsyncioTaskHandler` 收到信号后取消本地 asyncio 任务
4. 取消成功后调用 `stop_message_by_id()` 更新消息状态为 stopped

## 超时清理流程

1. 创建主任务时同时启动 `cleanup_task_after_timeout()`
2. 超时后发布取消信号到 PubSub
3. 主任务正常完成时取消对应的清理任务（通过 `cleanup_task_resources()`）

## 数据结构

```python
ACTIVE_ASYNCIO_TASKS: dict[str, dict[str, asyncio.Task]]  # {task_type: {task_id: Task}}
ACTIVE_CLEANUP_TASKS: dict[str, dict[str, asyncio.Task]]  # {task_type: {task_id: Task}}
```

## 配置

- `settings.workflow.task_cleanup_timeout`：超时清理时间（秒），默认 600
