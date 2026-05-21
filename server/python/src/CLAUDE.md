# CLAUDE.md

本文件为 Claude Code 在 Python 后端源码目录中工作时提供指导。

## 目录结构

```text
src/
├── demo/                      # Demo 业务模块
└── framework/                 # Framework 基础设施模块
```

## Demo 模块

Demo 模块是业务演示模块，采用 MVC 三层架构。

### 目录结构

```text
demo/
├── controllers/               # API 控制器
├── services/                  # 业务逻辑层
├── models/                    # SQLAlchemy 数据库模型
├── schemas/                   # Pydantic 校验模型
├── configs/                   # 配置管理
├── common/                    # 通用模块（异常、上下文等）
├── core/                      # 核心框架（路径、环境、单例等）
├── db/                        # 数据库引擎配置
├── migrations/                # Alembic 数据库迁移
├── utils/                     # 工具函数
├── examples/                  # 示例代码（LangChain、MCP 等）
├── listeners/                 # 消息监听器子模块
├── tasks/                     # 定时任务子模块
├── application_web.py         # FastAPI 应用入口
├── application_task.py        # 任务调度器入口
├── application_listener.py    # 消息监听器入口
└── run.py                     # Web 服务器启动入口
```

### MVC 编码模式

| 层级 | 职责 |
|------|------|
| Controller | HTTP 请求路由、参数解析、响应封装 |
| Service | 核心业务逻辑、数据库操作、事务管理 |
| Model | ORM 映射、数据库模型定义 |

### Controller 层规范

- **职责**：HTTP 请求路由，参数解析，调用 Service 层，返回响应
- **响应封装**：使用 `ORJSONResponse` 返回统一格式的 JSON 响应
- **数据转换**：通过 `Vo.model_validate()` 将 Model 转换为 VO

### Service 层规范

- **职责**：核心业务逻辑，数据库操作、事务管理
- **组织形式**：每个 Service 为一个类，模块底部实例化为单例
- **事务管理**：在 `try/except` 中执行，成功 `commit()`，异常 `rollback()`

### Model 层规范

- **ORM 基类**：继承 `BaseModel` + 所需的 Mixin
- **字段声明**：统一使用 `Mapped[type] = mapped_column(...)` 声明式注解

## Listeners 子模块

Listeners 模块提供消息监听能力，支持 Pub/Sub（广播）和 Queue（竞争消费）两种模式。

### 目录结构

```text
listeners/
├── __init__.py
├── setup.py                   # 生命周期管理
└── services/
    ├── pubsub/                # Pub/Sub 处理器
    │   ├── constants.py       # 主题常量
    │   └── heartbeat_handler.py
    └── queue/                 # Queue 处理器
        ├── constants.py       # 队列常量
        └── dataset_notify_handler.py
```

### 开发模式

**1. 创建处理器**

Pub/Sub 处理器继承 `SingleTopicHandler`：

```python
from framework.pubsub.handler import SingleTopicHandler

class MyHandler(SingleTopicHandler):
    topic: str = "my:topic"  # 订阅的主题

    async def handle(self, topic: str, message: dict) -> None:
        # 处理消息
        pass
```

Queue 处理器继承 `SingleQueueHandler`：

```python
from framework.queue.handler import SingleQueueHandler
from framework.core.queue import Message

class MyQueueHandler(SingleQueueHandler):
    queue: str = "my:queue"  # 消费的队列
    batch_size: int = 10

    async def handle(self, queue: str, messages: list[Message]) -> None:
        for message in messages:
            # 处理消息
            pass
```

**2. 定义常量**

在 `constants.py` 中定义主题/队列名称，禁止硬编码字符串：

```python
# services/pubsub/constants.py
MY_TOPIC = "my:topic"

# services/queue/constants.py
MY_QUEUE = "my:queue"
```

**3. 注册处理器**

在 `setup.py` 中注册：

```python
async def setup_listeners(settings: Settings) -> None:
    pubsub = get_pubsub_provider(settings.messaging)
    queue = get_queue_provider(settings.messaging)

    handler = MyHandler()
    await pubsub.subscribe(MY_TOPIC, handler.handle)
    await queue.create_consumer_group(MY_QUEUE, f"{MY_QUEUE}:group")
```

### 启动监听器

```bash
python manage.py runlistener
```

## Tasks 子模块

Tasks 模块提供定时任务调度能力，支持本地任务（每实例运行）和集群任务（唯一执行）。

### 目录结构

```text
tasks/
├── __init__.py
├── setup.py                   # 双调度器管理
└── services/
    ├── heartbeat_task.py      # 本地任务示例
    └── queue_status_task.py   # 集群任务示例
```

### 开发模式

**1. 创建任务函数**

所有任务都是异步函数，必须捕获异常：

```python
from loguru import logger

_logger = logger.bind(name=__name__)

async def my_task() -> None:
    try:
        # 任务逻辑
        _logger.info("任务执行")
    except Exception:
        _logger.exception("任务执行异常")
```

**2. 注册任务**

在 `setup.py` 中声明式注册：

```python
# 本地任务: (func, task_id, trigger_args)
local_tasks = [
    (heartbeat_task, "demo_heartbeat", {"seconds": 60}),
]

# 集群任务: (func, task_id, trigger, trigger_args)
cluster_tasks = [
    (queue_status_task, "demo_queue_status", "interval", {"minutes": 5}),
]
```

**3. 调度器说明**

- **本地调度器**：MemoryJobStore，每个实例独立运行
- **集群调度器**：RedisJobStore，集群中只有一个实例执行

### 启动调度器

```bash
python manage.py runtask
```

### 添加新任务

1. 在 `services/` 下创建任务文件
2. 在 `setup.py` 中导入并添加到 `local_tasks` 或 `cluster_tasks`
3. 编写单元测试和集成测试

## Framework 模块

Framework 模块提供统一的基础设施组件。

### 目录结构

```text
framework/
├── config/                    # 统一配置模块
├── cache/                     # Redis 缓存模块
├── core/                      # 核心接口定义
├── common/                    # 通用组件
├── storage/                   # 存储实现
├── queue/                     # 队列实现
├── lock/                      # 分布式锁
├── pubsub/                    # 发布订阅
├── database/                  # 数据库组件
├── tenant/                    # 租户模型
└── utils/                     # 工具函数
```

### 核心功能

| 组件 | 用途 |
|------|------|
| config | YAML 配置加载、环境变量覆盖 |
| cache | Redis 缓存操作封装 |
| storage | 对象存储（MinIO、阿里云 OSS） |
| lock | 分布式锁实现 |
| queue | 消息队列封装 |
| pubsub | 发布订阅模式 |
| database | 数据库基础模型和 Mixin |
| tenant | 多租户数据隔离 |

### 设计模式

**Protocol 接口定义：**

```python
from typing import Protocol

class StorageProvider(Protocol):
    async def upload(self, bucket: str, name: str, data: bytes) -> str: ...
    async def download(self, bucket: str, name: str) -> bytes: ...
```

**工厂模式：**

```python
def get_storage_provider(config: OssSettings) -> StorageProvider:
    match config.default_type:
        case "minio": return MinioStorage(config.minio)
        case "aliyun": return AliyunStorage(config.aliyun)
```

### 快速使用

**配置加载：**

```python
from framework.configs import init_settings, get_settings

settings = init_settings("path/to/config")
print(settings.server.port)
```

**Redis 缓存：**

```python
from framework.cache.redis_util import RedisUtil

await RedisUtil.init(redis_config)
await RedisUtil.set("key", "value", ttl=60)
value = await RedisUtil.get("key")
```

**分布式锁：**

```python
from framework.lock import get_lock_provider

lock_provider = get_lock_provider(settings.lock)
async with lock_provider.acquire_context("resource_key", ttl=30) as lock:
    if lock:
        # 执行业务逻辑
        pass
```

## API 端点

- **`/health`** - 健康检查
- **`/api/v1/datasets`** - 知识库 CRUD 示例
- **`/docs`** - Swagger API 文档
- **`/redoc`** - ReDoc API 文档

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](../tests/CLAUDE.md)。
