## Why

当前 `demo` 模块中的配置、缓存、存储等基础设施代码分散且耦合，难以复用。需要一个统一的 `framework` 模块来提供可复用的基础设施组件，支持多技术栈（Python 优先），使其他业务模块能够直接使用这些通用能力。

## What Changes

- 创建 `framework` 模块，包含统一配置、缓存、存储、队列、发布订阅、锁、数据库、租户、工具类等子模块
- 从 `demo` 模块提取可复用代码到 `framework`，实现关注点分离
- 基于 Python Protocol 定义核心接口，支持多种实现方式
- 创建统一的 `RedisUtil` 工具类，简化 Redis 操作
- 实现配置驱动的组件加载（OSS、Messaging、Lock）
- 迁移 Alon 参考项目的成熟实现（configs、common、database、utils）
- 重构 `demo` 模块，使其依赖 `framework`
- 为所有迁移功能编写单元测试

## Capabilities

### New Capabilities

- `config`: 统一配置模块，基于 YAML 文件的配置加载和 Pydantic 验证
- `cache`: 统一缓存模块，包含 RedisUtil 工具类和连接管理
- `core`: 核心接口定义，使用 Python Protocol 定义 Storage/Queue/PubSub/Lock 接口
- `common`: 通用模块，包含异常、上下文、响应等基础组件
- `storage`: 存储实现模块，支持 MinIO/阿里云/腾讯云 对象存储
- `queue`: 队列实现模块，基于 Redis Stream 的消息队列
- `pubsub`: 发布订阅模块，基于 Redis PubSub
- `lock`: 分布式锁模块，基于 Redis 实现
- `database`: 数据库通用模块，包含 Base/Mixins/Types/Tree/Interceptors/Events
- `tenant`: 多租户模型设计（仅模型，不含实现）
- `utils`: 工具函数模块，包含字符串、时间日期、列表、枚举等工具

### Modified Capabilities

无现有能力修改

## Impact

- **新增目录**: `server/python/src/framework/` 及其子模块
- **新增测试**: `server/python/src/tests/framework/`
- **重构模块**: `server/python/src/demo/` 将依赖 `framework`
- **配置文件**: 复用现有 `server/config/application.yml`
- **依赖**: 可能需要新增 `aiocache`、`minio` 等 Python 包
