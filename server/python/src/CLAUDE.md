# Python 源码开发指南

本文件为 Claude Code 在 `server/python/src/` 源码目录中工作时提供指导。

## 目录定位

`src/` 按顶级模块组织源码。模块是 `src/{module}/`，功能是模块内的子域；不要把功能域提升为新的顶级目录。

## 顶级模块

| 模块 | 定位 | 详细文档 |
| --- | --- | --- |
| `demo/` | AI 助手平台业务演示模块，包含知识库、示例代码、任务和监听器 | 暂无模块级 CLAUDE.md，参考本文件通用规则 |
| `framework/` | 底层基础设施模块，提供配置、缓存、数据库、存储、队列、发布订阅、锁、多租户、工具能力 | [framework/CLAUDE.md](framework/CLAUDE.md) |
| `iam/` | 身份认证与权限模块，提供租户、用户、认证、角色、权限和资源配置能力 | [iam/CLAUDE.md](iam/CLAUDE.md) |

入口文件：

| 文件 | 用途 |
| --- | --- |
| `application_web.py` | FastAPI Web 应用装配入口 |
| `application_task.py` | 定时任务调度器入口 |
| `application_listener.py` | 消息监听器入口 |
| `run.py` | Web 服务启动入口 |

## 通用分层规则

业务模块遵循 MVC / 分层结构：

| 层级 | 目录 | 职责 |
| --- | --- | --- |
| Controller | `controllers/` | HTTP 路由、请求参数、鉴权依赖、响应封装 |
| Service | `services/` | 业务规则、事务边界、跨模型协作、外部组件调用 |
| Model | `models/` | SQLAlchemy ORM 映射、数据库约束、领域枚举 |
| Schema | `schemas/` | Pydantic 请求 DTO、响应 VO、内部数据结构 |
| Migration | `migrations/` | Alembic 迁移、seed、迁移模板 |

## 开发约定

- 新模块放在 `src/{module}/`，不要放在 `src/core/`、`src/common/` 等跨模块目录；可复用基础能力应进入 `framework/`。
- Controller 不直接写复杂业务逻辑和数据库事务。
- Service 是主要业务逻辑入口，涉及写操作时明确事务提交与回滚策略。
- Model 字段使用 SQLAlchemy 2.0 声明式类型：`Mapped[...] = mapped_column(...)`。
- Schema 不复用 ORM 模型作为 API 响应，使用 Pydantic 模型表达边界数据。
- 模块内的迁移、seed、初始化逻辑应与模块代码同目录维护。
- 业务模块可以依赖 framework；framework 禁止依赖业务模块。

## Demo 子域

Demo 模块除常规 MVC 目录外，还包含：

| 子域 | 职责 |
| --- | --- |
| `examples/` | LangChain、LangGraph、MCP、插件、RAG 等示例代码 |
| `listeners/` | 消息监听器，支持 Pub/Sub 和 Queue 两类消费模式 |
| `tasks/` | 定时任务，区分本地任务和集群唯一任务 |
| `utils/` | Demo 专属工具函数 |
| `configs/`、`core/`、`common/` | Demo 历史通用能力，新增跨模块基础能力优先放入 framework |

### 监听器开发

- Pub/Sub 处理器继承 framework 的 `SingleTopicHandler`。
- Queue 处理器继承 framework 的 `SingleQueueHandler`。
- 主题名和队列名放在 `constants.py`，不要硬编码在处理逻辑中。
- 新处理器需要在 `listeners/setup.py` 注册。

### 任务开发

- 任务函数使用 async，内部捕获并记录异常。
- 本地任务每个实例独立执行；集群任务通过共享 JobStore 保证唯一执行。
- 新任务需要在 `tasks/setup.py` 注册，并补充对应测试。

## API 入口

常见接口包括：

| 路径 | 用途 |
| --- | --- |
| `/health` | 健康检查 |
| `/api/v1/datasets` | Demo 知识库 CRUD 示例 |
| `/admin/v1/tenants` | IAM 管理后台租户接口 |
| `/console/v1/tenants` | IAM 用户端租户接口 |
| `/docs` | Swagger API 文档 |
| `/redoc` | ReDoc API 文档 |

以实际路由注册为准。新增或修改接口时，同时检查 Controller、Schema、Service、权限和测试。

## 测试入口

源码修改后优先运行对应模块测试。测试目录说明见 [../tests/CLAUDE.md](../tests/CLAUDE.md)。
