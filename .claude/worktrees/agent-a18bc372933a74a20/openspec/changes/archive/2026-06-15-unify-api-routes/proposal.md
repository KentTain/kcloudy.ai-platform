## 为什么

当前 API 路由结构存在以下问题：

1. **路由规则不统一**：`/admin/v1/iam/users` 带 `iam` 模块名，而 `/admin/v1/tenants` 不带 `tenant` 模块名，难以从 URL 直接判断所属模块
2. **模块边界模糊**：`/admin/v1/system-settings` 同时存在于 IAM 和 Tenant 模块，但路径相同容易混淆
3. **AI 模块路由特殊**：`/api/v1/chat-messages` 破坏了三层结构约定（admin/console/inner）
4. **中间件路径判断复杂**：当前通过硬编码路径前缀判断模块归属，扩展性差

此次变更旨在建立清晰的模块优先路由规则，使 API 设计一致、可预测，并支持按模块加载中间件。

## 变更内容

### 路由规则变更 **BREAKING**

**新路由规则**：`/{模块}/{类型}/v1/{功能}/{其他}`

- **模块**：`tenant`、`iam`、`ai`
- **类型**：`admin`（管理端）、`console`（用户端）、`inner`（内部接口）

**示例变更**：

| 当前路由 | 新路由 |
|---------|--------|
| `/admin/v1/iam/users` | `/iam/admin/v1/users` |
| `/admin/v1/tenants` | `/tenant/admin/v1/tenants` |
| `/console/v1/iam/auth/login` | `/iam/console/v1/auth/login` |
| `/api/v1/chat-messages` | `/ai/console/v1/chat-messages` |
| `/inner/v1/users/{id}` | `/iam/inner/v1/users/{id}` |

### 中间件加载策略变更

- **`/tenant/admin/*`**：使用 `AdminAuthMiddleware`（租户管理员 Token）
- **`/tenant/console/*`**：使用 `IAMAuthMiddleware`（JWT Token，与 IAM 共享用户体系）
- **`/iam/*`**：使用 `IAMAuthMiddleware`（JWT Token）
- **`/ai/*`**：使用 `IAMAuthMiddleware`（复用 IAM 认证体系）
- **`/*/inner/*`**：无认证（模块间内部调用）

### 移除的路由规则

- **移除** `/api/v1/*` 前缀，统一到模块优先结构

## 功能 (Capabilities)

### 新增功能

无新增功能。此次变更为架构重构，不引入新功能。

### 修改功能

- `api-routes`: API 路由规则从类型优先变更为模块优先，影响所有模块的 Controller 路由定义
- `module-middleware`: 中间件加载策略从全局硬编码路径判断变更为按模块前缀加载

## 影响

### 后端影响

| 模块 | 影响范围 | 文件数量 |
|------|---------|---------|
| Tenant | Controller 路由定义、AdminAuthMiddleware 路径判断 | 约 6 个文件 |
| IAM | Controller 路由定义、IAMAuthMiddleware 路径判断 | 约 12 个文件 |
| AI | Controller 路由定义、模块路由注册 | 约 6 个文件 |
| Framework | application_web.py 中间件注册逻辑 | 1 个文件 |

**总计**：约 25 个后端文件需要修改

### 前端影响

| 模块 | 影响范围 | 文件数量 |
|------|---------|---------|
| Tenant | API 调用路径、client.ts Token 选择逻辑 | 约 5 个文件 |
| IAM | API 调用路径 | 约 6 个文件 |
| AI | API 调用路径、useChat composable | 约 4 个文件 |
| Framework | client.ts Token 选择逻辑 | 1 个文件 |

**总计**：约 16 个前端文件需要修改

### 文档影响

- `server/CLAUDE.md`：新增「API 路由规范」章节
- 各模块 `CLAUDE.md`：更新路由表

### 兼容性

**破坏性变更**：所有 API 路径发生变化，前后端必须同步更新。

**迁移策略**：采用一次性变更，同时修改后端路由和前端 API 调用，不保留旧路由兼容。
