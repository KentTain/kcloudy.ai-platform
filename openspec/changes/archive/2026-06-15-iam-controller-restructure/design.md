## 上下文

IAM 模块当前有 8 个 controller 散落在 `controllers/` 根目录，部分已按 admin/console/inner 分类的（system_setting、inner 层）与未分类的混存。路由注册使用 `/api/v1/iam` 前缀，与项目约定（admin=`/admin/v1`，console=`/console/v1`，inner=`/inner/v1`）不一致。前端 API 路径也需同步调整。

Tenant 模块已完成按约定分类，可作为参考模式。

## 目标 / 非目标

**目标：**

- 将根目录 controller 按职责拆分到 admin/console/inner 子目录
- 统一路由前缀为约定格式（admin/console/inner）
- 路径命名统一为复数形式（users、roles、permissions、departments、menus）
- 合并重叠的 menu controller
- 更新 module.py 路由注册
- 同步更新前端 API 路径

**非目标：**

- 不修改 Service 层和 Model 层代码
- 不修改 Schema（Pydantic 模型）定义
- 不修改 inner 层已有的 controller
- 不修改 admin/system_setting_controller 和 console/system_setting_controller
- 不涉及数据库迁移
- 不引入新的业务功能

## 决策

### 决策 1：Controller 拆分策略

**选择**：按 admin/console 职责拆分 user_controller 和 menu_controller，其余 controller 整体移入对应子目录。

**理由**：user_controller 同时包含用户端接口（`/me`、`/password`、`/register`）和管理员接口（CRUD、状态管理、角色分配），必须拆分。menu_controller 的 `/user` 端点与 user_menu_controller 重叠，需合并。

**备选方案**：
- 保持单文件，仅加注释区分 → 职责混合，权限边界模糊，不可取
- 按资源拆分（auth/user/role 等），不按 admin/console 拆 → 不符合项目约定

### 决策 2：菜单端点合并策略

**选择**：保留 `user_menu_service.get_user_menus` 实现（有租户感知），合并到 `console/user_controller.py` 的 `GET /menus` 端点。删除 `menu_controller` 的 `GET /user` 端点和 `user_menu_controller` 文件。

**理由**：`user_menu_service` 接收 `tenant_id` 参数，能正确处理多租户菜单过滤，而 `menu_service.get_user_menus` 缺少租户感知。

### 决策 3：路由前缀与路径命名

**选择**：
- Admin 层：`/admin/v1/iam` + 复数资源名（`/users`、`/roles`、`/permissions`、`/departments`、`/menus`）
- Console 层：`/console/v1/iam` + 复数资源名
- Inner 层：保持现有 `/inner/v1` 和 `/inner/v1/iam` 不变

**理由**：与 tenant 模块保持一致；复数形式是 REST 惯例，表示资源集合。

### 决策 4：controllers/__init__.py 处理

**选择**：清空旧路由注册，`__init__.py` 仅保留模块级文档字符串。路由注册全部由 `module.py` 管理。

**理由**：当前 `__init__.py` 创建了 `/iam` 前缀的路由组并注册所有子路由，这与 `module.py` 的注册机制重复。按 tenant 模块的模式，每个 controller 独立导出 router，由 `module.py` 统一注册。

## 风险 / 权衡

- **[BREAKING CHANGE] API 路径全部变更** → 需前后端同步发布，不存在渐进迁移路径（因旧路径无消费者需兼容）
- **旧路径无灰度期** → 项目处于开发阶段，可直接切换，无需版本共存
- **console/user_controller 端点路径可能冲突** → auth 子路径（`/auth/login`）与 users 子路径（`/users/me`）在同一个 `/console/v1/iam` 前缀下注册，需要独立 router 实例，由 module.py 分别挂载
