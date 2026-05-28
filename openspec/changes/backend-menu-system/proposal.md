## 为什么

当前前端框架直接导入业务模块路由，违反依赖倒置原则。为实现前端模块化架构，需要后端提供动态菜单 API，支持按权限动态加载菜单树，配合前端模块系统的菜单 Store 实现模块解耦。

## 变更内容

### 新增

- 菜单模型（Menu）：支持树形结构、图标、路径、权限关联
- 菜单-权限关联模型（MenuPermission）：多对多关系
- 菜单服务（MenuService）：菜单 CRUD、树形查询、权限过滤
- 菜单 API（/admin/v1/menus）：管理端菜单管理接口
- 数据库迁移脚本：创建菜单表和关联表
- 菜单种子数据：初始化默认菜单结构

## 功能 (Capabilities)

### 新增功能

- `menu-management`: 菜单管理功能，包含菜单模型、服务、API 和数据库迁移

### 修改功能

（无）

## 影响

### 代码影响

- 新增文件：
  - `server/python/src/iam/models/menu.py`
  - `server/python/src/iam/models/menu_permission.py`
  - `server/python/src/iam/services/menu_service.py`
  - `server/python/src/iam/controllers/menu_controller.py`
  - `server/python/src/demo/migrations/versions/xxxx_add_menu_tables.py`

### API 影响

- 新增端点 `/admin/v1/menus`：菜单 CRUD 操作
- 新增端点 `/admin/v1/menus/tree`：获取菜单树
- 新增端点 `/admin/v1/menus/user`：获取当前用户的菜单

### 数据库影响

- 新增表 `iam_menu`：菜单主表
- 新增表 `iam_menu_permission`：菜单-权限关联表

### 依赖影响

- 复用现有 `BaseModel`、`TreeNodeMixin`（`framework/database/mixins/tree.py`）
- 复用现有 `Permission`、`Role` 模型关联
