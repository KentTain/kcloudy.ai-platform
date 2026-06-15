## 为什么

IAM 模块的 controller 未按照项目约定的 admin/console/inner 三层分类组织。当前 8 个 controller 散落在 `controllers/` 根目录，职责混合（如 user_controller 同时包含用户端和管理员接口），路由前缀不统一（使用 `/api/v1/iam` 而非约定的 `/admin/v1` 和 `/console/v1`），导致代码难以维护、权限边界模糊。

## 变更内容

- **将根目录 controller 按职责拆分到 admin/console/inner 子目录**，与 tenant 模块保持一致
- **统一路由前缀**：admin 接口使用 `/admin/v1/iam`，console 接口使用 `/console/v1/iam`，inner 接口保持 `/inner/v1`
- **统一路径命名为复数形式**：`/users`、`/roles`、`/permissions`、`/departments`、`/menus`
- **合并重叠 controller**：menu_controller 的 `/user` 端点和 user_menu_controller 合并到 console/user_controller
- **删除根目录旧 controller** 和 `controllers/__init__.py` 中的旧路由注册
- **更新 module.py 路由注册**，按 admin/console/inner 分层注册
- **更新前端 API 调用路径**，对齐新的后端路由

**BREAKING**：所有前端 API 路径变更，需同步更新。

## 功能 (Capabilities)

### 新增功能

- `iam-admin-api`: IAM 管理后台 API（用户管理、角色管理、权限管理、部门管理、菜单管理），路由前缀 `/admin/v1/iam`
- `iam-console-api`: IAM 用户端 API（认证、OAuth、个人信息管理、用户菜单），路由前缀 `/console/v1/iam`

### 修改功能

（无现有规范级需求变更，此次为纯结构调整）

## 影响

- **后端**：`server/python/src/iam/controllers/` 目录结构重组，删除 8 个根目录旧文件，新建 8 个分类文件
- **后端**：`server/python/src/iam/module.py` 路由注册方式变更
- **前端**：`web/vue/src/iam/api/` 下 6 个 API 文件的请求路径全部变更
- **API 兼容性**：所有 IAM 相关 API 路径变更，属于 **BREAKING CHANGE**，需前后端同步发布
- **无数据库变更**：本次调整不涉及数据库迁移
