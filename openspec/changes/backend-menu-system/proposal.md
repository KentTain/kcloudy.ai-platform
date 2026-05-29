## 为什么

前端模块分离方案需要后端驱动的菜单系统，当前 framework 直接依赖业务模块违反依赖倒置原则。菜单系统是模块独立部署的关键基础设施，支持跨子域名的菜单导航和权限控制。

## 变更内容

### 新增

- **Menu 模型**：菜单实体，继承 `BaseModel` 和 `TreeNodeMixin`，支持树形结构
- **MenuPermission 模型**：菜单-权限关联，实现 RBAC 菜单可见性控制
- **Menu API**：`GET /api/v1/menus/user` 返回当前用户可见菜单树
- **IAM 迁移重建**：按 `MODULE_SCHEMA = "iam"` 重建所有表
- **Demo 迁移重建**：按 `MODULE_SCHEMA = "demo"` 重建所有表
- **菜单种子数据**：初始化默认菜单配置

### 修复

- **IAM/Demo env.py**：修复配置导入错误，统一使用 `framework.configs`

## 功能 (Capabilities)

### 新增功能

- `menu-system`: 菜单管理功能，包含菜单模型、API、权限关联和种子数据

### 修改功能

无现有功能的需求变更。

## 影响

### 代码影响

| 模块 | 影响 |
|------|------|
| `iam/models/` | 新增 `menu.py`，包含 Menu 和 MenuPermission 模型 |
| `iam/controllers/` | 新增 `menu_controller.py` |
| `iam/services/` | 新增 `menu_service.py` |
| `iam/migrations/versions/` | 新建迁移文件，重建 IAM 表结构 |
| `iam/migrations/seeds/` | 新增 `menu_seed.py` |
| `demo/migrations/versions/` | 新建迁移文件，重建 Demo 表结构 |
| `demo/migrations/seeds/` | 新增种子数据（如有） |

### API 影响

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/menus/user` | GET | 新增：获取当前用户可见菜单树 |

### 数据库影响

| Schema | 变更 |
|--------|------|
| `iam` | 重建所有表（users, roles, permissions, departments 等），新增 menus、menu_permissions 表 |
| `demo` | 重建所有表（datasets 等） |

### 迁移策略

**完全重建**（无生产数据）：
1. 执行 `manage.py db rebuild --module iam`
2. 执行 `manage.py db rebuild --module demo`
3. 执行 `manage.py seed --module iam`
4. 执行 `manage.py seed --module demo`

### 依赖关系

- Menu 模型依赖 `TreeNodeMixin`（`framework/database/mixins/tree.py`）
- MenuPermission 复用现有 Permission 模型
- 菜单 API 依赖用户认证中间件
