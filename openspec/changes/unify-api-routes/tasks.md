## 1. 后端模块路由注册更新

- [x] 1.1 更新 Tenant 模块路由注册（`tenant/module.py` 的 `get_routers()` 方法）
- [x] 1.2 更新 IAM 模块路由注册（`iam/module.py` 的 `get_routers()` 方法）
- [x] 1.3 创建或更新 AI 模块路由注册（`ai/module.py` 的 `get_routers()` 方法）

## 2. Tenant 模块 Controller 路由变更

- [x] 2.1 更新 `tenant/controllers/admin/tenant_controller.py` 路由路径
- [x] 2.2 更新 `tenant/controllers/admin/tenant_module_controller.py` 路由路径
- [x] 2.3 更新 `tenant/controllers/admin/module_controller.py` 路由路径
- [x] 2.4 更新 `tenant/controllers/admin/resource_config_controller.py` 路由路径
- [x] 2.5 更新 `tenant/controllers/console/tenant_controller.py` 路由路径
- [x] 2.6 更新 `tenant/controllers/inner/tenant_controller.py` 路由路径

## 3. IAM 模块 Controller 路由变更

- [x] 3.1 更新 `iam/controllers/admin/user_controller.py` 路由路径
- [x] 3.2 更新 `iam/controllers/admin/role_controller.py` 路由路径
- [x] 3.3 更新 `iam/controllers/admin/permission_controller.py` 路由路径
- [x] 3.4 更新 `iam/controllers/admin/department_controller.py` 路由路径
- [x] 3.5 更新 `iam/controllers/admin/menu_controller.py` 路由路径
- [x] 3.6 更新 `iam/controllers/admin/system_setting_controller.py` 路由路径
- [x] 3.7 更新 `iam/controllers/console/auth_controller.py` 路由路径
- [x] 3.8 更新 `iam/controllers/console/oauth_controller.py` 路由路径
- [x] 3.9 更新 `iam/controllers/console/user_controller.py` 路由路径
- [x] 3.10 更新 `iam/controllers/console/system_setting_controller.py` 路由路径
- [x] 3.11 更新 `iam/controllers/inner/user_controller.py` 路由路径
- [x] 3.12 更新 `iam/controllers/inner/department_controller.py` 路由路径
- [x] 3.13 更新 `iam/controllers/inner/tenant_menu_controller.py` 路由路径
- [x] 3.14 更新 `iam/controllers/inner/tenant_permission_controller.py` 路由路径
- [x] 3.15 更新 `iam/controllers/inner/tenant_role_controller.py` 路由路径

## 4. AI 模块 Controller 路由变更

- [x] 4.1 更新 `ai/controllers/admin/plugin.py` 路由路径
- [x] 4.2 更新 `ai/controllers/console/plugin.py` 路由路径
- [x] 4.3 更新 `ai/controllers/inner/plugin.py` 路由路径
- [x] 4.4 更新 `ai/controllers/v1/chat/llm.py` 路由路径
- [x] 4.5 更新 `ai/controllers/v1/conversation.py` 路由路径
- [x] 4.6 更新 `ai/controllers/v1/model.py` 路由路径

## 5. 后端中间件更新

- [x] 5.1 更新 `AdminAuthMiddleware` 路径匹配逻辑（匹配 `/tenant/admin/*`）
- [x] 5.2 更新 `AdminAuthMiddleware` 豁免路径（`/tenant/admin/v1/auth/login`）
- [x] 5.3 更新 `IAMAuthMiddleware` 路径匹配逻辑（匹配 `/iam/*`、`/ai/*`、`/tenant/console/*`）
- [x] 5.4 更新 `IAMAuthMiddleware` 豁免路径（`/iam/console/v1/auth/login` 等）
- [x] 5.5 更新 `application_web.py` 中间件注册逻辑

## 6. 前端 Framework API 更新

- [x] 6.1 更新 `framework/api/client.ts` Token 选择逻辑（按模块前缀选择 Token 类型）
- [x] 6.2 更新 `framework/api/menu.ts` API 路径

## 7. 前端 Tenant 模块 API 更新

- [x] 7.1 更新 `tenant/api/admin.ts` API 路径
- [x] 7.2 更新 `tenant/api/tenant.ts` API 路径
- [x] 7.3 更新 `tenant/api/module.ts` API 路径
- [x] 7.4 更新 `tenant/api/tenantModule.ts` API 路径

## 8. 前端 IAM 模块 API 更新

- [x] 8.1 更新 `iam/api/user.ts` API 路径
- [x] 8.2 更新 `iam/api/role.ts` API 路径
- [x] 8.3 更新 `iam/api/permission.ts` API 路径
- [x] 8.4 更新 `iam/api/department.ts` API 路径
- [x] 8.5 更新 `iam/api/menu.ts` API 路径
- [x] 8.6 更新 `iam/api/auth.ts` API 路径

## 9. 前端 AI 模块 API 更新

- [x] 9.1 更新 `ai/api/conversation.ts` API 路径
- [x] 9.2 更新 `ai/api/model.ts` API 路径
- [x] 9.3 更新 `ai/composables/useChat.ts` API 端点
- [x] 9.4 更新 `ai/pages/ChatPage.vue` API 端点参数

## 10. 文档更新

- [x] 10.1 更新 `server/CLAUDE.md` 新增「API 路由规范」章节
- [x] 10.2 更新 `server/python/CLAUDE.md` 模块路由说明
- [x] 10.3 更新 `server/python/src/tenant/CLAUDE.md` 路由表
- [x] 10.4 更新 `server/python/src/iam/CLAUDE.md` 路由表
- [x] 10.5 更新 `server/python/src/ai/CLAUDE.md` 路由表（如存在）
- [x] 10.6 更新 `web/CLAUDE.md` API 调用规范
- [x] 10.7 更新 `web/vue/CLAUDE.md` baseURL 说明

## 11. 验证测试

- [x] 11.1 验证后端服务启动正常
- [x] 11.2 验证前端开发服务器启动正常
- [x] 11.3 验证 Tenant 管理端登录和 API 调用
- [x] 11.4 验证 IAM 用户端登录和 API 调用
- [x] 11.5 验证 AI 对话功能
