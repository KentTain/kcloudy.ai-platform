## 1. 基础设施与工具

- [x] 1.1 创建 `framework/utils/crypto.py`，实现 BCrypt 密码哈希和验证函数
- [x] 1.2 创建 `framework/utils/jwt.py`，实现 JWT Token 生成和验证函数
- [x] 1.3 创建 `framework/utils/session.py`，实现 Redis 会话管理（创建、获取、删除、黑名单）

## 2. 数据模型迁移与创建

- [x] 2.1 创建 `demo/models/iam/` 目录结构
- [x] 2.2 迁移 `Tenant` 模型到 `demo/models/iam/tenant.py`
- [x] 2.3 迁移 `TenantConfig` 模型到 `demo/models/iam/tenant_config.py`
- [x] 2.4 迁移 `TenantAdmin` 模型到 `demo/models/iam/tenant_admin.py`
- [x] 2.5 迁移 `UserTenant` 模型到 `demo/models/iam/user_tenant.py`
- [x] 2.6 创建 `demo/models/iam/user.py`，定义 User 模型
- [x] 2.7 创建 `demo/models/iam/oauth_connection.py`，定义 OAuthConnection 模型
- [x] 2.8 创建 `demo/models/iam/department.py`，定义 Department 和 UserDepartment 模型
- [x] 2.9 创建 `demo/models/iam/role.py`，定义 Role 模型
- [x] 2.10 创建 `demo/models/iam/permission.py`，定义 Permission、UserRole、RolePermission 模型
- [x] 2.11 创建 `demo/models/iam/enums.py`，定义用户状态、OAuth 提供商等枚举
- [x] 2.12 更新 `demo/models/__init__.py`，导出 iam 模块模型

## 3. 数据库迁移

- [x] 3.1 创建迁移文件，新增 `users` 表
- [x] 3.2 创建迁移文件，新增 `oauth_connections` 表
- [x] 3.3 创建迁移文件，新增 `departments`、`user_departments` 表
- [x] 3.4 创建迁移文件，新增 `roles`、`permissions`、`user_roles`、`role_permissions` 表
- [x] 3.5 创建种子脚本，初始化预定义角色和权限
- [x] 3.6 创建种子脚本，初始化默认租户管理员

## 4. Pydantic Schema 定义

- [x] 4.1 创建 `demo/schemas/iam/login.py`，定义登录请求/响应模型
- [x] 4.2 创建 `demo/schemas/iam/token.py`，定义 Token 响应模型
- [x] 4.3 创建 `demo/schemas/iam/user.py`，定义用户相关请求/响应模型
- [x] 4.4 创建 `demo/schemas/iam/role.py`，定义角色相关请求/响应模型
- [x] 4.5 创建 `demo/schemas/iam/permission.py`，定义权限相关请求/响应模型
- [x] 4.6 创建 `demo/schemas/iam/department.py`，定义部门相关请求/响应模型
- [x] 4.7 创建 `demo/schemas/iam/oauth.py`，定义 OAuth 相关请求/响应模型

## 5. 用户认证服务实现

- [x] 5.1 创建 `demo/services/iam/auth_service.py`，实现登录逻辑（用户名/邮箱/手机号）
- [x] 5.2 实现密码验证和 BCrypt 比对
- [x] 5.3 实现 Token 生成（Access Token + Refresh Token）
- [x] 5.4 实现 Token 刷新逻辑
- [x] 5.5 实现登出逻辑（Token 黑名单）
- [x] 5.6 实现登录限流检查

## 6. 用户管理服务实现

- [x] 6.1 创建 `demo/services/iam/user_service.py`，实现用户注册
- [x] 6.2 实现密码强度校验
- [x] 6.3 实现获取当前用户信息
- [x] 6.4 实现修改用户信息
- [x] 6.5 实现修改密码
- [x] 6.6 实现密码重置（发送验证码、重置密码）

## 7. RBAC 服务实现

- [x] 7.1 创建 `demo/services/iam/role_service.py`，实现角色 CRUD
- [x] 7.2 创建 `demo/services/iam/permission_service.py`，实现权限查询
- [x] 7.3 实现角色-权限关联管理
- [x] 7.4 实现用户-角色关联管理
- [x] 7.5 实现权限检查逻辑（支持通配符）

## 8. 组织架构服务实现

- [x] 8.1 创建 `demo/services/iam/department_service.py`，实现部门 CRUD
- [x] 8.2 实现部门树形结构查询
- [x] 8.3 实现用户-部门关联管理
- [x] 8.4 实现部门负责人设置

## 9. OAuth 服务实现

- [x] 9.1 创建 `demo/services/iam/oauth_service.py`，实现 OAuth 配置管理
- [x] 9.2 实现微信 OAuth2 授权链接生成
- [x] 9.3 实现微信 OAuth2 回调处理（获取 Token、用户信息）
- [x] 9.4 实现企微 OAuth2 授权链接生成
- [x] 9.5 实现企微 OAuth2 回调处理
- [x] 9.6 实现 OAuth 用户自动注册与绑定
- [x] 9.7 实现用户信息补全功能

## 10. 控制器实现

- [x] 10.1 创建 `demo/controllers/iam/auth_controller.py`，实现登录/登出/Token 刷新接口
- [x] 10.2 创建 `demo/controllers/iam/user_controller.py`，实现用户管理接口
- [x] 10.3 创建 `demo/controllers/iam/role_controller.py`，实现角色管理接口
- [x] 10.4 创建 `demo/controllers/iam/permission_controller.py`，实现权限查询接口
- [x] 10.5 创建 `demo/controllers/iam/department_controller.py`，实现部门管理接口
- [x] 10.6 创建 `demo/controllers/iam/oauth_controller.py`，实现 OAuth 登录接口
- [x] 10.7 注册路由到 FastAPI 应用

## 11. 认证中间件

- [x] 11.1 创建 `demo/middlewares/iam_auth_middleware.py`，实现 Token 验证中间件
- [x] 11.2 实现权限检查装饰器 `@require_permission`
- [x] 11.3 实现权限缓存机制

## 12. 单元测试

- [x] 12.1 创建 `tests/demo/unit/iam/test_crypto.py`，测试加密工具函数
- [x] 12.2 创建 `tests/demo/unit/iam/test_jwt.py`，测试 JWT 工具函数
- [x] 12.3 创建 `tests/demo/unit/iam/test_auth_service.py`，测试认证服务
- [x] 12.4 创建 `tests/demo/unit/iam/test_user_service.py`，测试用户管理服务
- [x] 12.5 创建 `tests/demo/unit/iam/test_role_service.py`，测试角色服务
- [x] 12.6 创建 `tests/demo/unit/iam/test_department_service.py`，测试部门服务

## 13. 集成测试

- [x] 13.1 创建 `tests/demo/integration/iam/test_auth_flow.py`，测试登录/登出/刷新流程
- [x] 13.2 创建 `tests/demo/integration/iam/test_user_flow.py`，测试用户注册/修改流程
- [x] 13.3 创建 `tests/demo/integration/iam/test_rbac_flow.py`，测试权限控制流程
- [x] 13.4 创建 `tests/demo/integration/iam/test_oauth_flow.py`，测试 OAuth 登录流程

## 14. 文档与配置

- [x] 14.1 更新 `pyproject.toml`，添加 bcrypt、PyJWT 依赖
- [x] 14.2 更新配置文件，添加 JWT 密钥、Token 有效期等配置项
- [x] 14.3 更新 API 文档（OpenAPI Schema 自动生成）
