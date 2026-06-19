## Context

当前项目采用模块化单体架构，每个业务模块拥有独立的 PostgreSQL schema。IAM 模块目前承载了三个职责：
1. 用户身份认证（Authentication）
2. 访问控制（Authorization / RBAC）
3. 租户管理（Multi-tenancy）

租户作为多租户系统的基础设施概念，被错误地绑定在 IAM 模块中。这导致：
- 职责边界模糊，IAM 模块过于庞大
- 其他业务模块（如 demo）需要租户信息时，必须依赖 IAM 模块
- 无法独立部署租户服务供多个业务系统共享

### 当前状态

```
src/iam/
├── models/
│   ├── tenant.py, tenant_config.py, tenant_admin.py  # 应迁移
│   ├── user_tenant.py                                 # 保留
│   └── user.py, role.py, permission.py, department.py
├── controllers/
│   ├── admin/tenant_controller.py                     # 应迁移
│   └── console/tenant_controller.py                   # 应迁移
└── services/
    ├── tenant_service.py                              # 应迁移
    └── tenant_provider_impl.py                        # 应迁移
```

### 约束

- 遵循现有模块化单体架构模式
- 每个模块独立的 PostgreSQL schema
- 跨模块调用通过 Protocol 或内部接口
- 前端模块结构与后端对齐

## Goals / Non-Goals

**Goals:**

1. 创建独立的 `tenant` 模块，包含租户核心功能
2. 精简 `iam` 模块，聚焦身份认证和访问控制
3. 引入 `/inner/v1/*` 内部接口层，支持模块间调用
4. 实现混合调用模式（单体直接调用，微服务 HTTP 调用）
5. 前端同步拆分 tenant 模块

**Non-Goals:**

1. 不改变现有租户数据结构和业务逻辑
2. 不实现租户服务的独立部署（仅做架构准备）
3. 不修改 `framework.tenant` 的 Protocol 定义
4. 不实现微服务模式的服务间认证（单体模式无需认证）

## Decisions

### 决策 1：模型归属划分

| 模型 | 归属 | 理由 |
|------|------|------|
| `Tenant` | tenant | 租户核心实体，独立于 IAM |
| `TenantConfig` | tenant | 租户资源配置，与 Tenant 一对一 |
| `TenantAdmin` | tenant | 全局管理员，不属于任何租户 |
| `UserTenant` | iam | 用户-租户关联，与 User 强耦合 |

**替代方案：** 将 `UserTenant` 也迁移到 tenant 模块
**选择理由：** `UserTenant` 是用户和租户的关联表，业务上更贴近用户管理（如分配用户到租户），放在 IAM 模块更合理

### 决策 2：接口分层架构

```
/admin/v1/*     → 管理后台接口（全局/租户管理员）
/console/v1/*   → 用户控制台接口（登录用户）
/api/v1/*       → 通用业务接口（RESTful CRUD）
/inner/v1/*     → 内部接口（模块间调用）  ← 新增
```

**关键区别：**
- `console` 面向前端用户，依赖 Token 上下文
- `inner` 面向其他模块，参数显式传递，不依赖 Token

**替代方案：** 使用 Protocol 注入方式（当前 TenantProvider 模式）
**选择理由：** inner 接口更灵活，支持未来微服务部署，且批量操作更方便

### 决策 3：混合调用模式

```python
# demo/clients/iam_client.py
class IamClient:
    @staticmethod
    async def get_user(user_id: str) -> UserInfo:
        if settings.IAM_INNER_URL:  # 微服务模式
            return await InnerHttpClient.get(f"{settings.IAM_INNER_URL}/users/{user_id}")
        else:  # 单体模式
            from iam.services import UserService
            return await UserService.get_by_id(user_id)
```

**替代方案：** 仅使用一种调用方式
**选择理由：** 同时支持两种模式，单体部署时零网络开销，微服务部署时无需代码修改

### 决策 4：数据库 Schema 分布

```
PostgreSQL: demo_db
├── schema: tenant     # 新增
│   ├── tenants
│   ├── tenant_configs
│   ├── tenant_admins
│   └── alembic_version
├── schema: iam
│   ├── user_tenants   # 保留，跨 schema 引用
│   └── ...
└── schema: demo
    └── ...
```

**跨 schema 引用策略：** 不使用数据库外键约束，由应用层一致性检查

**替代方案：** 使用跨 schema 外键
**选择理由：** 避免迁移复杂性，Alembic autogenerate 对跨 schema 外键支持有限

### 决策 5：迁移顺序

1. tenant 模块迁移（创建 schema 和表）
2. iam 模块迁移（更新 user_tenants）
3. demo 模块迁移（无变更）

**策略：** 通过 `module.py` 的 `dependencies` 声明强制顺序

## Risks / Trade-offs

### 风险 1：迁移数据丢失

**风险：** 拆分过程中租户数据可能丢失或损坏

**缓解措施：**
- 先备份数据库
- 在测试环境验证迁移脚本
- 提供回滚脚本

### 风险 2：模块间调用失败

**风险：** inner 接口调用失败导致业务中断

**缓解措施：**
- inner 接口添加健康检查端点
- Client 封装添加重试机制
- 单体模式下直接调用 Service，无网络风险

### 风险 3：前端路由冲突

**风险：** 路由拆分后可能产生冲突

**缓解措施：**
- 路由统一在 framework 注册
- 保持路由路径不变（`/admin/tenants` 仍然有效）

### 风险 4：测试覆盖不足

**风险：** 拆分后功能回归问题

**缓解措施：**
- 拆分前补充集成测试
- 拆分后运行全量测试

### Trade-off

| 选择 | 获益 | 代价 |
|------|------|------|
| 拆分 tenant 模块 | 职责清晰，支持独立部署 | 迁移成本，模块间调用复杂度 |
| 新增 inner 接口层 | 支持微服务模式 | 额外代码量 |
| 不使用跨 schema 外键 | 迁移简单 | 应用层需保证一致性 |
