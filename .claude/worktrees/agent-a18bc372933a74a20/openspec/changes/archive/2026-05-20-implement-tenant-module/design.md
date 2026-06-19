## Context

当前项目是一个多技术栈 AI 助手平台演示项目，Python 后端采用 FastAPI + SQLAlchemy 2.0，遵循三层架构（Controller → Service → Model）。项目已有部分多租户基础设施实现（TenantMixin、TenantEventListener），但缺少完整的租户上下文管理、中间件、缓存策略和 API 端点。

**已有实现：**
- `server/python/src/framework/tenant/models.py` - 租户模型
- `server/python/src/framework/tenant/context.py` - 租户上下文
- `server/python/src/framework/database/mixins/tenant.py` - TenantMixin
- `server/python/src/framework/database/events/tenant.py` - TenantEventListener

**缺失实现：**
- 租户中间件（解析、验证、注入）
- Redis 多资源隔离（缓存、队列、发布订阅、锁）
- MinIO 存储隔离
- 两级缓存策略
- 异步任务上下文传递
- 管理后台 API
- 用户端 API

## Goals / Non-Goals

**Goals:**
- 实现完整的租户上下文管理（ContextVar 存储、请求级隔离）
- 实现租户中间件，支持多种租户解析策略（Header > Token > 用户默认）
- 实现数据库字段级隔离，业务代码无感知
- 实现 Redis 多资源隔离（缓存、队列、发布订阅、锁）
- 实现 MinIO 存储隔离
- 实现两级缓存策略（L1 本地 + L2 Redis）
- 实现异步任务租户上下文传递
- 实现管理后台 API（独立认证、跨租户管理）
- 实现用户端租户 API（列表、当前、切换）
- 实现默认租户管理员自动初始化

**Non-Goals:**
- 不实现独立数据库隔离策略（Shared Database, Shared Schema）
- 不实现租户配额管理
- 不实现租户计费功能
- 不实现租户自定义域名
- 不实现前端租户切换 UI

## Decisions

### 1. 数据库隔离策略：字段级隔离（Shared Database, Shared Schema）

**选择原因：**
- 实现简单，运维成本低
- 资源共享方便，连接池管理简单
- 跨租户查询（管理员场景）容易实现
- 适合中小规模 SaaS 应用

**替代方案：**
- 独立数据库（每个租户一个数据库）：运维成本高，跨租户查询复杂
- 独立 Schema（共享数据库，独立 Schema）：折中方案，仍需管理多个 Schema

### 2. Redis 隔离策略：Key 前缀隔离

**选择原因：**
- 实现简单，无需额外 Redis 实例
- 工具类层面自动注入，业务代码无感知
- 支持 `skip_tenant=True` 跳过前缀（管理员场景）

**Key 格式：**
- 缓存：`{tenant_id}:{business_key}`
- 队列：`{tenant_id}:queue:{queue_name}`
- 发布订阅：`{tenant_id}:channel:{channel_name}`
- 锁：`{tenant_id}:lock:{resource_key}`

### 3. 存储隔离策略：共享 Bucket + 租户目录隔离

**选择原因：**
- 单 Bucket 管理简单
- 自动拼接租户目录前缀
- 预签名 URL 包含租户路径

**路径格式：** `{tenant_id}/{category}/{filename}`

### 4. 租户缓存策略：两级缓存（L1 本地 + L2 Redis）

**选择原因：**
- L1 本地缓存减少 Redis 访问
- L2 Redis 缓存跨实例共享
- 缓存失效通过 Redis Pub/Sub 同步

**缓存配置：**
- L1：进程级缓存，最大 1000 条，无 TTL
- L2：Redis 缓存，TTL 5 分钟

### 5. 异步任务上下文传递：消息携带 tenant_id

**选择原因：**
- 任务入队时自动记录 tenant_id
- 任务执行时自动恢复租户上下文
- 任务处理完成后清理上下文

### 6. 管理后台：独立路由前缀 + 独立认证

**选择原因：**
- 不经过租户中间件
- 支持跨租户查询与操作
- 独立的超级管理员认证体系

## Risks / Trade-offs

### 风险 1：租户上下文泄漏
- **风险**：请求结束后未清理上下文，导致下一个请求获取到错误的租户信息
- **缓解**：使用 `try/finally` 确保上下文清理，中间件层面强制清理

### 风险 2：跨租户数据访问
- **风险**：业务代码绕过框架直接访问数据库，导致跨租户数据泄漏
- **缓解**：代码审查时检查直接使用 `session.execute()` 的代码，强制使用 Repository 层

### 风险 3：缓存不一致
- **风险**：多实例部署时，L1 本地缓存不一致
- **缓解**：通过 Redis Pub/Sub 发布缓存失效消息，收到消息后清除 L1 缓存

### 风险 4：异步任务上下文丢失
- **风险**：异步任务执行时租户上下文丢失
- **缓解**：任务入队时序列化 tenant_id，执行时自动恢复上下文

### Trade-off 1：字段级隔离 vs 独立数据库
- **选择**：字段级隔离
- **代价**：无法实现物理级数据隔离，安全性略低
- **收益**：运维成本低，实现简单

### Trade-off 2：两级缓存 vs 单级缓存
- **选择**：两级缓存
- **代价**：实现复杂度增加，需要处理缓存一致性
- **收益**：性能提升，减少 Redis 访问

## Migration Plan

### 阶段 1：基础设施（Week 1）
1. 完善租户模型（Tenant、TenantConfig、TenantAdmin、UserTenant）
2. 实现租户上下文（TenantContext）
3. 实现租户中间件（TenantMiddleware）
4. 实现租户解析器（TenantResolver）

### 阶段 2：数据隔离（Week 2）
1. 完善 TenantMixin 和 TenantEventListener
2. 实现 Redis 多资源隔离（RedisUtil 改造）
3. 实现 MinIO 存储隔离（StorageService 改造）
4. 实现两级缓存（TenantCache）

### 阶段 3：API 实现（Week 3）
1. 实现管理后台 API（TenantAdminController）
2. 实现用户端 API（TenantController）
3. 实现默认租户管理员初始化
4. 编写集成测试

### 阶段 4：异步任务支持（Week 4）
1. 实现任务队列租户上下文传递
2. 实现任务执行器上下文恢复
3. 编写异步任务测试

### 数据库迁移
```sql
-- 创建租户表
CREATE TABLE tenants (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    expired_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建租户配置表
CREATE TABLE tenant_configs (
    id VARCHAR(32) PRIMARY KEY,
    tenant_id VARCHAR(32) NOT NULL REFERENCES tenants(id),
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, config_key)
);

-- 创建租户管理员表
CREATE TABLE tenant_admins (
    id VARCHAR(32) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户租户关联表
CREATE TABLE user_tenants (
    id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    tenant_id VARCHAR(32) NOT NULL REFERENCES tenants(id),
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tenant_id)
);

-- 为现有业务表添加 tenant_id 字段
ALTER TABLE users ADD COLUMN tenant_id VARCHAR(32) REFERENCES tenants(id);
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
```

### 回滚策略
1. 移除租户中间件
2. 清理租户相关代码
3. 删除租户相关数据库表
4. 移除业务表的 tenant_id 字段

## Open Questions

1. **租户 ID 生成策略**：使用 UUID 还是自定义规则？
   - 建议：使用 `tenant_` 前缀 + 时间戳 + 随机数，如 `tenant_20240101_abc123`

2. **租户过期处理**：过期租户是软删除还是硬删除？
   - 建议：软删除，保留数据以便恢复

3. **租户配额**：是否需要限制租户的资源使用（用户数、存储空间等）？
   - 建议：本期不实现，后续扩展

4. **租户自定义配置**：配置项存储在租户配置表还是配置文件？
   - 建议：存储在数据库 tenant_configs 表，支持动态修改
