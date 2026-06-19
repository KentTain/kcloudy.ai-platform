# Demo 模块开发指南

本文件为 Claude Code 在 `src/demo/` 业务演示模块中工作时提供指导。

## 模块定位

Demo 模块是 AI 助手平台的业务演示模块，包含知识库管理、健康检查、AI 示例（LangChain、LangGraph、MCP）等功能。它是业务模块，可以依赖 framework 和 tenant 模块。

## 依赖边界

```
Demo ──▶ framework（基础设施）
Demo ──▶ tenant（通过 inner 接口获取租户信息）
```

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器 |
| services/ | 知识库、健康检查等业务逻辑 |
| models/ | 知识库等数据库模型 |
| schemas/ | 请求、响应 Pydantic 模型 |
| migrations/ | 数据库迁移与种子数据 |
| examples/ | LangChain、LangGraph、MCP 示例代码 |
| listeners/ | 消息监听器（Pub/Sub 和 Queue 模式） |
| tasks/ | 定时任务（本地任务和集群唯一任务） |

## 接口分层

| 前缀 | 用途 |
|------|------|
| /api/v1/datasets | 知识库 CRUD |
| /health | 健康检查 |

## 监听器开发

- Pub/Sub 处理器继承 framework 的 `SingleTopicHandler`
- Queue 处理器继承 framework 的 `SingleQueueHandler`
- 主题名和队列名放在 `constants.py`
- 新处理器需在 `listeners/setup.py` 注册

## 任务开发

- 任务函数使用 async，内部捕获并记录异常
- 本地任务每个实例独立执行；集群任务通过共享 JobStore 保证唯一执行
- 新任务需在 `tasks/setup.py` 注册

## 开发规则

- Controller 只处理路由、参数校验和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- Model 使用 framework 的数据库基类、Mixin

## 测试

```bash
uv run pytest tests/demo/ -v
```
