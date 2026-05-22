## Context

### 当前状态

1. **TenantMiddleware 已实现但未注册**：`framework/tenant/middleware.py` 中的 TenantMiddleware 完整实现了 X-Tenant-Id 解析、租户验证、上下文注入，但 application_web.py 中未挂载

2. **seed 初始化不自动**：tenant_seed.py 和 admin_seed.py 需要手动执行 `manage.py seed`，应用启动时不会自动初始化

3. **管理员 hash 不一致**：
   - `iam/middlewares/admin_auth_middleware.py` 使用 `hashlib.sha256`
   - `iam/migrations/seeds/admin_seed.py` 使用 `framework.utils.crypto.hash_password`（实际是 bcrypt）

4. **角色体系不完整**：已有 TenantAdmin（租户管理员）模型，但：
   - 租户管理员与 Tenant 无关联
   - 缺少系统管理员（Tenant 内最高权限）和普通用户的权限体系
   - Demo 模块（Dataset）未实现租户隔离

### 约束

- 三种角色：租户管理员（TenantAdmin）、系统管理员（User + Role）、普通用户（User）
- 租户管理员负责创建租户和管理租户级系统管理员
- 系统管理员负责管理本租户的组织架构、用户、角色、权限
- 普通用户使用系统业务功能

## Goals / Non-Goals

**Goals:**
- 注册 TenantMiddleware，使 X-Tenant-Id 解析生效
- 自动执行 seed 初始化（租户、角色、权限、管理员）
- 统一管理员密码 hash 函数
- 为默认租户配置物理隔离资源（数据库、存储、缓存）
- Demo 模块 Dataset 实现租户数据隔离
- 实现三级角色权限体系

**Non-Goals:**
- 不实现租户管理员创建租户的后台 UI
- 不实现多租户数据库物理隔离的连接切换逻辑（仅配置存储）
- 不修改现有 API 端点路径

## Decisions

### D1: TenantMiddleware 挂载位置

**选择**：在 application_web.py 的 create_app() 中通过 app.add_middleware() 挂载

**备选**：
- 在 lifespan 中手动添加（写法繁琐）
- 通过装饰器方式（不符合 FastAPI 惯例）

**理由**：FastAPI 标准做法，中间件顺序在 IAMAuthMiddleware 之后

### D2: 管理员 hash 函数统一方案

**选择**：统一使用 `framework.utils.crypto.hash_password`（bcrypt）

**备选**：
- 统一使用 SHA-256（简单但不够安全）
- 在 TenantAdminInitializer 中从 middleware 导入 hash_password

**理由**：framework.utils.crypto 是项目统一的密码处理工具，支持 bcrypt 更安全

### D3: Seed 初始化时机

**选择**：在 application_web.py 的 lifespan 中顺序调用

**备选**：
- 通过 FastAPI lifespan events
- 通过独立的 init 命令

**理由**：lifespan 是应用级别初始化入口，顺序执行保证依赖关系（租户 → 角色 → 权限 → 管理员）

### D4: 角色体系设计

**选择**：
- TenantAdmin：租户管理员，独立表，系统初始化时创建
- User + Role：系统管理员/普通用户，通过 UserTenant 关联租户

**备选**：
- 三种角色都放在 User 表（字段冗余）
- 三种角色都放在 TenantAdmin 表（职责不清）

**理由**：TenantAdmin 是平台级管理员，User 是租户内用户，职责分离清晰

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| TenantMiddleware 在 IAMAuthMiddleware 之后，可能覆盖用户上下文 | 租户上下文可能不生效 | 中间件顺序：AdminAuth → IAMAuth → Tenant |
| 首次部署时数据库为空，seed 可能失败 | 应用无法启动 | 使用 try-catch 捕获异常，记录日志但不阻止启动 |
| 默认租户资源配置为空 | 租户无物理隔离 | 提供配置模板，默认创建逻辑隔离租户 |

## Migration Plan

1. **数据库迁移**：执行 alembic 创建 tenant_configs 表（如需要）
2. **配置文件**：更新 application-local.yml 添加默认租户配置
3. **重启服务**：lifespan 自动执行 seed
4. **验证**：调用 GET /api/v1/datasets 带 X-Tenant-Id 验证隔离

## Open Questions

- [ ] 是否需要为默认租户预配置物理隔离资源（db_name/storage_bucket/cache_db）？
- [ ] 租户管理员登录后的 Token 是否需要持久化到 Redis？
- [ ] Demo 模块的租户隔离是否需要修改现有 Dataset API 的响应格式？
