## Why

Framework 模块当前仅有单元测试（使用 mock），缺乏对真实基础设施服务的集成验证。当实际连接 Redis、PostgreSQL、MinIO 时可能存在未被发现的兼容性或配置问题。集成测试将确保各组件在真实环境下的正确性和可靠性。

## What Changes

- 在 `tests/framework/` 目录下新增集成测试模块
- 为以下组件添加集成测试：
  - `cache` - Redis 缓存真实连接测试
  - `lock` - Redis 分布式锁真实连接测试
  - `queue` - Redis Stream 队列真实连接测试
  - `pubsub` - Redis 发布订阅真实连接测试
  - `storage` - MinIO 对象存储真实连接测试
  - `database` - PostgreSQL 数据库真实连接测试
- 添加集成测试专用 fixture 和配置
- 添加测试标记区分单元测试与集成测试

## Capabilities

### New Capabilities

- `framework-integration-tests`: Framework 模块集成测试能力，验证各基础设施组件与真实服务的交互

### Modified Capabilities

无现有 spec 修改，这是新增测试能力。

## Impact

- **测试目录**: `server/python/tests/framework/` 新增集成测试文件
- **测试配置**: 需要添加集成测试专用 fixture 和环境配置
- **CI/CD**: 需要配置集成测试运行环境（Redis、PostgreSQL、MinIO 服务）
- **测试标记**: 使用 `@pytest.mark.integration` 区分集成测试
