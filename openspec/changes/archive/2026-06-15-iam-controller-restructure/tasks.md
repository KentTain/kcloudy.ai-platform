## 1. 后端 Admin 层 Controller 创建

- [x] 1.1 创建 `controllers/admin/user_controller.py`：从根目录 `user_controller.py` 拆出管理员端点（列表/创建/详情/更新/删除/状态管理/密码重置/角色分配/部门分配），路由路径改为复数形式 `/users`
- [x] 1.2 创建 `controllers/admin/role_controller.py`：移入根目录 `role_controller.py`，路由路径改为 `/roles`
- [x] 1.3 创建 `controllers/admin/permission_controller.py`：移入根目录 `permission_controller.py`，路由路径改为 `/permissions`
- [x] 1.4 创建 `controllers/admin/department_controller.py`：移入根目录 `department_controller.py`，路由路径改为 `/departments`
- [x] 1.5 创建 `controllers/admin/menu_controller.py`：移入根目录 `menu_controller.py` 的 `GET ""` 端点，路由路径改为 `/menus`，删除 `GET /user` 端点

## 2. 后端 Console 层 Controller 创建

- [x] 2.1 创建 `controllers/console/auth_controller.py`：移入根目录 `auth_controller.py`，路由路径改为 `/auth`
- [x] 2.2 创建 `controllers/console/oauth_controller.py`：移入根目录 `oauth_controller.py`，路由路径改为 `/oauth`
- [x] 2.3 创建 `controllers/console/user_controller.py`：从根目录 `user_controller.py` 拆出用户端端点（注册/当前用户/修改信息/密码管理）+ 合并 `user_menu_controller.py` 的 `GET /menus` 端点，路由路径改为 `/users`

## 3. 后端路由注册与清理

- [x] 3.1 更新 `controllers/__init__.py`：清除旧路由注册，仅保留模块级文档字符串
- [x] 3.2 更新 `module.py` 的 `get_routers()` 方法：按 admin/console/inner 分层注册新 controller，admin 前缀 `/admin/v1/iam`，console 前缀 `/console/v1/iam`
- [x] 3.3 删除根目录旧 controller 文件：`auth_controller.py`、`user_controller.py`、`role_controller.py`、`permission_controller.py`、`department_controller.py`、`menu_controller.py`、`oauth_controller.py`、`user_menu_controller.py`

## 4. 前端 API 路径更新

- [x] 4.1 更新 `web/vue/src/iam/api/auth.ts`：认证相关路径改为 `/console/v1/iam/auth/...`，用户信息路径改为 `/console/v1/iam/users/...`
- [x] 4.2 更新 `web/vue/src/iam/api/user.ts`：用户管理路径改为 `/admin/v1/iam/users/...`
- [x] 4.3 更新 `web/vue/src/iam/api/role.ts`：角色路径改为 `/admin/v1/iam/roles/...`
- [x] 4.4 更新 `web/vue/src/iam/api/permission.ts`：权限路径改为 `/admin/v1/iam/permissions/...`
- [x] 4.5 更新 `web/vue/src/iam/api/department.ts`：部门路径改为 `/admin/v1/iam/departments/...`
- [x] 4.6 更新 `web/vue/src/iam/api/menu.ts`：菜单路径改为 `/admin/v1/iam/menus`

## 5. 验证

- [x] 5.1 启动后端服务验证所有新路由正确注册（检查 /docs 端点列表）
- [x] 5.2 验证前端页面功能正常（登录、用户管理、角色管理、部门管理、菜单管理）
