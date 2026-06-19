## 1. 迁移环境修复

- [x] 1.1 修复 `iam/migrations/env.py` 配置导入（`demo.configs` → `framework.configs`）
- [x] 1.2 修复 `demo/migrations/env.py` 配置导入（`demo.configs` → `framework.configs`）

## 2. Menu 模型实现

- [x] 2.1 创建 `iam/models/menu.py`，实现 Menu 模型（BaseModel + TreeNodeMixin）
- [x] 2.2 创建 `iam/models/menu.py`，实现 MenuPermission 模型
- [x] 2.3 更新 `iam/models/__init__.py`，导出 Menu 和 MenuPermission

## 3. Menu Schema 实现

- [x] 3.1 创建 `iam/schemas/menu.py`，实现 MenuTreeNode 响应模型
- [x] 3.2 创建 `iam/schemas/menu.py`，实现 MenuListResponse 响应模型

## 4. Menu Service 实现

- [x] 4.1 创建 `iam/services/menu_service.py`，实现 `get_user_menus` 方法

## 5. Menu Controller 实现

- [x] 5.1 创建 `iam/controllers/menu_controller.py`，实现 `GET /api/v1/menus/user` 端点
- [x] 5.2 更新 `iam/controllers/__init__.py`，注册 menu_router

## 6. IAM 迁移重建

- [x] 6.1 创建 `iam/migrations/versions/001_iam_tables.py`，重建 IAM 所有表
- [x] 6.2 创建 `iam/migrations/versions/001_iam_tables.py`，包含 menus 和 menu_permissions 表

## 7. Demo 迁移重建

- [x] 7.1 创建 `demo/migrations/versions/001_demo_tables.py`，重建 Demo 所有表

## 8. 种子数据

- [x] 8.1 创建 `iam/migrations/seeds/menu_seed.py`，初始化默认菜单数据
- [x] 8.2 更新 `iam/module.py`，注册 menu_seed

## 9. 测试验证

- [x] 9.1 执行 `manage.py db migrate --module tenant` 验证 Tenant 迁移
- [x] 9.2 执行 `manage.py db migrate --module iam` 验证 IAM 迁移
- [x] 9.3 执行 `manage.py db migrate --module demo` 验证 Demo 迁移
- [x] 9.4 执行 `manage.py seed --module iam` 验证种子数据
- [x] 9.5 验证数据完整性（权限 13 条、角色 3 个、菜单 7 个、菜单权限关联 4 条）
