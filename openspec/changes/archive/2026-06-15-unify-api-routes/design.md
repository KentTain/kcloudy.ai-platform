## 上下文

### 当前状态

**路由结构混乱**：

```
/admin/v1/iam/users        → 带 iam 模块名
/admin/v1/tenants          → 不带 tenant 模块名
/admin/v1/system-settings  → IAM 和 Tenant 共用路径
/api/v1/chat-messages      → AI 模块特殊路由，破坏三层结构
```

**中间件路径判断**：

```python
# 当前硬编码路径判断
TENANT_ADMIN_API_PREFIXES = [
    "/admin/v1/iam",
    "/admin/v1/system-settings",
]

# 需要硬编码豁免路径
EXEMPT_PATHS = {
    "/api/console/v1/iam/auth/login",
    "/console/v1/iam/auth/login",
    # ... 更多硬编码路径
}
```

### 约束

1. **向后兼容性**：不需要保持旧路由兼容，采用一次性变更
2. **前端 baseURL**：保持单一 `/api` 前缀，通过 Vite 代理到后端
3. **认证体系**：Tenant 管理员和 IAM 用户使用不同的 Token 体系

### 利益相关者

- 后端开发者：需要更新所有 Controller 路由定义
- 前端开发者：需要更新所有 API 调用路径
- 运维人员：需要了解 API 路由结构变化

## 目标 / 非目标

**目标：**

1. 建立 **模块优先** 的统一路由规则：`/{模块}/{类型}/v1/{功能}`
2. 实现中间件 **按模块前缀自动加载**，消除硬编码路径判断
3. 统一 AI 模块路由到三层结构（admin/console/inner）
4. 更新文档，建立清晰的路由规范

**非目标：**

1. 不引入新的认证机制或 Token 格式变更
2. 不修改业务逻辑或数据模型
3. 不保留旧路由的向后兼容

## 决策

### 决策 1：路由规则采用模块优先设计

**选择**：`/{模块}/{类型}/v1/{功能}`

**理由**：

- 模块边界清晰，URL 即知所属模块
- 中间件可按模块前缀加载（`/tenant/*` vs `/iam/*`）
- 微服务拆分时，模块可独立部署到不同域名

**替代方案**：

| 方案 | 示例 | 优劣势 |
|------|------|--------|
| 类型优先（当前） | `/admin/v1/iam/users` | 业界主流，但模块边界不清晰 |
| 模块优先（选择） | `/iam/admin/v1/users` | 模块边界清晰，支持按模块加载中间件 |

### 决策 2：中间件按模块前缀加载

**选择**：中间件根据路径前缀自动选择认证方式

```python
# 中间件加载策略
PATH_PREFIXES = {
    "/tenant/admin/": "AdminAuthMiddleware",   # 租户管理员 Token
    "/tenant/console/": "IAMAuthMiddleware",   # JWT Token
    "/iam/": "IAMAuthMiddleware",              # JWT Token
    "/ai/": "IAMAuthMiddleware",               # JWT Token（复用 IAM）
}
```

**理由**：

- 消除硬编码路径判断
- 新增模块只需在配置中添加映射
- 与路由规则对齐

**替代方案**：

| 方案 | 优劣势 |
|------|--------|
| 全局中间件 + 路径判断（当前） | 硬编码路径，扩展性差 |
| 模块级中间件注册（选择） | 按模块前缀自动选择，扩展性好 |
| 路由级依赖注入 | 每个路由单独配置，维护成本高 |

### 决策 3：`/tenant/console/*` 使用 IAMAuthMiddleware

**选择**：`/tenant/console/*` 路由使用 IAMAuthMiddleware（JWT Token）

**理由**：

- 租户控制台用户来自 IAM 用户体系
- 与 `/iam/console/*`、`/ai/console/*` 共享认证逻辑
- 只有 `/tenant/admin/*` 需要独立的租户管理员 Token

**替代方案**：

| 方案 | 优劣势 |
|------|--------|
| 独立认证 | 需要单独登录流程，用户体验差 |
| 复用 IAM（选择） | 统一用户体系，简化实现 |

### 决策 4：前端保持单一 baseURL

**选择**：前端保持 `baseURL: /api`，完整路径包含模块名

```typescript
// 前端 API 调用示例
get("/iam/admin/v1/users")
get("/tenant/console/v1/tenants/current")
get("/ai/console/v1/chat-messages")
```

**理由**：

- 保持现有前端架构不变
- 路径变更通过替换字符串完成
- Vite 代理无需修改

**替代方案**：

| 方案 | 示例 | 优劣势 |
|------|------|--------|
| 单一 baseURL（选择） | `baseURL: /api`，路径含模块 | 简单，无需修改架构 |
| 按模块配置 baseURL | `iamClient: { baseURL: '/api/iam' }` | 更灵活，但增加复杂度 |

## 风险 / 权衡

### 风险 1：前后端同步变更

**风险**：前后端必须同时部署，否则 API 调用失败

**缓解措施**：

- 采用一次性变更策略，同一次发布包含所有变更
- 部署前确保所有测试通过
- 使用蓝绿部署，减少停机时间

### 风险 2：遗漏的路由变更

**风险**：部分路由未更新，导致 404 错误

**缓解措施**：

- 使用 grep 搜索所有 `/admin/v1`、`/console/v1`、`/inner/v1`、`/api/v1` 路径
- 编写自动化测试覆盖所有 API 端点
- 变更清单详细列出所有受影响文件

### 风险 3：第三方集成影响

**风险**：外部系统依赖当前 API 路径

**缓解措施**：

- 当前项目为演示平台，无外部集成
- 未来如有外部集成，提供版本化 API（`/v2/`）

### 权衡：非主流路由设计

**权衡**：模块优先路由非业界主流

**接受理由**：

- 项目为演示平台，无需遵循大厂规范
- 模块优先设计更清晰，适合模块化架构
- 团队内部约定，无需对外解释

## 实施步骤

### 阶段 1：后端路由变更

1. 更新 `tenant/module.py`、`iam/module.py`、`ai/module.py` 的 `get_routers()` 方法
2. 更新所有 Controller 文件的路由装饰器（`@router.get` 等）
3. 更新中间件路径判断逻辑

### 阶段 2：前端 API 变更

1. 更新 `framework/api/client.ts` 的 Token 选择逻辑
2. 更新所有模块 API 文件的路径定义
3. 更新 `useChat` 等 composable 的 API 端点

### 阶段 3：文档更新

1. 更新 `server/CLAUDE.md` 新增「API 路由规范」章节
2. 更新各模块 `CLAUDE.md` 的路由表

## 开放问题

无。所有关键决策已明确。
