## 为什么

当前系统存在两套独立的上下文管理机制（TenantContext 和 Context），导致用户信息无法在生产环境正常工作，且租户信息分散存储存在不一致风险。统一上下文管理是解决用户信息缺失、消除双重存储问题的关键步骤。

## 变更内容

### 核心变更
- **统一上下文存储**：将用户信息和租户信息统一存储到 Context（基于 ContextVar）
- **改造 TenantContext**：将 TenantContext 改造为 Context 的适配器，保持向后兼容
- **同步用户信息**：在 IAMAuthMiddleware 中将 JWT 用户信息同步到 Context

### 中间件重构
- **TenantMiddleware**：移除测试用户逻辑，专注于租户解析
- **IAMAuthMiddleware**：验证 JWT 并同步用户信息到 Context，验证租户归属
- **新增 TestUserMiddleware**：开发测试专用，支持 X-Test-User-Id 请求头（仅非生产环境）

### **BREAKING** 破坏性变更
- 移除 TenantMiddleware 中的 X-User-Id 支持（替换为 X-Test-User-Id）
- TenantContext 底层存储从独立的 _tenant_context 改为共享的 _context_var

## 功能 (Capabilities)

### 新增功能
- test-user-context: 开发测试场景下的用户上下文模拟，通过 X-Test-User-Id 请求头注入测试用户

### 修改功能
- user-context: 用户上下文管理需求变更，从依赖注入和 ContextVar 混合模式改为统一 ContextVar 管理
- tenant-context: 租户上下文管理需求变更，从独立 ContextVar 改为共享 Context 的适配器

## 影响

### 代码影响
- framework/common/ctx.py: Context 类扩展，新增 tenant_name、tenant_code 等字段
- framework/tenant/context.py: TenantContext 改造为适配器
- framework/tenant/middleware.py: 移除测试用户逻辑
- iam/middlewares/iam_auth_middleware.py: 同步用户信息到 Context
- framework/middlewares/test_user_middleware.py: 新增测试用户中间件
- application_web.py: 调整中间件注册顺序

### API 端点影响
- 无 API 端点变更（内部架构重构）

### 兼容性影响
- **向后兼容**：TenantContext API 保持不变，现有代码无需修改
- **测试影响**：使用 X-User-Id 的测试需改为 X-Test-User-Id

### 数据库影响
- 无数据库变更
