## Why

当前 IAM 模块的多租户架构存在多个关键缺口：TenantMiddleware 未注册到应用导致 X-Tenant-Id 解析机制失效、seed 初始化不会自动执行导致首次部署需要手动操作、默认租户缺少资源配置、三种角色（租户管理员/系统管理员/普通用户）的权限体系未完全落地。这些问题会导致租户隔离无法正常工作，影响生产环境部署。

## What Changes

- **注册 TenantMiddleware**：在 application_web.py 中挂载租户中间件，启用 X-Tenant-Id 请求头解析和上下文注入
- **统一管理员 hash 函数**：修复 TenantAdminInitializer 与 admin_seed.py 使用不同 hash 函数的问题
- **自动执行 seed**：在 lifespan 中增加租户和 IAM 数据的自动初始化
- **默认租户资源配置**：从 TenantSettings 读取配置创建带物理隔离资源的默认租户
- **demo 模块租户集成**：Dataset 模型添加 TenantMixin，Service 层实现租户数据过滤
- **角色权限体系落地**：实现租户管理员、系统管理员、普通用户三级角色及其权限继承

## Capabilities

### New Capabilities

- **tenant-context-injection**: 实现 X-Tenant-Id 请求头解析、租户状态验证、上下文注入的完整流程
- **tenant-seed-initialization**: 应用启动时自动创建默认租户、角色、权限数据
- **role-permission-hierarchy**: 实现租户管理员/系统管理员/普通用户三级角色及权限继承
- **tenant-resource-config**: 支持为租户配置独立的数据库、存储、缓存资源
- **demo-tenant-isolation**: demo 模块知识库数据按租户隔离

### Modified Capabilities

- （无，现有的 iam 模块 spec 需新增）

## Impact

- **核心组件**：application_web.py、iam/initializers/、framework/tenant/middleware.py
- **数据库**：新增租户资源配置表（已有 Tenant 模型，需确认字段完整）
- **API 变更**：无新增 API，现有 API 行为受租户上下文影响
- **兼容性**：首次部署需要迁移脚本创建默认数据
