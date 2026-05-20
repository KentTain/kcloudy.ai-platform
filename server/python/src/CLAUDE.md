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
