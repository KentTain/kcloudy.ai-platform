## 上下文

前端模块分离方案需要后端驱动的菜单系统。当前系统存在以下问题：

1. **Framework 直接依赖业务模块**：`framework/router/index.ts` 硬编码导入 `demoRoutes`、`iamRoutes`
2. **缺少菜单权限控制**：菜单配置在前端硬编码，无法根据用户权限动态显示
3. **不支持跨模块菜单**：模块独立部署后，需要跨子域名导航

参考设计文档：`docs/designs/前端Vue的模块分离设计方案.md`

### 约束

- Menu 模型归属 IAM 模块，存储在 `iam` schema
- 复用现有 RBAC 权限体系（Permission、Role）
- 使用 `TreeNodeMixin` 支持菜单树形结构
- 遵循三层架构：Controller → Service → Model

## 目标 / 非目标

**目标：**

- 创建 Menu 和 MenuPermission 模型，支持树形菜单结构和权限关联
- 提供 `GET /api/v1/menus/user` API 返回用户可见菜单树
- 支持 `deployment_base_url` 字段标记跨模块菜单
- 重建 IAM 和 Demo 模块的迁移，确保表归属正确的 schema

**非目标：**

- 菜单的 CRUD 管理界面（后续变更）
- 前端菜单渲染逻辑（前端变更）
- Docker 部署配置（部署变更）

## 决策

### 决策 1：菜单关联权限而非角色

**选择：** 菜单 → Permission → Role（方案 B）

**理由：**
- 复用现有 RBAC 权限模型，不破坏统一权限体系
- 支持菜单关联多个权限（查看菜单需要任一权限）
- 权限变更自动反映到菜单可见性

**替代方案：**
- 方案 A：菜单直接关联角色 → 简单但破坏 RBAC 统一性

### 决策 2：Menu 继承 TreeNodeMixin

**选择：** 使用 `framework.database.mixins.tree.TreeNodeMixin`

**理由：**
- 提供完整的树形结构支持（parent_id、tree_level、tree_sort 等）
- 与现有 Department 模型保持一致
- 自动维护树字段，减少手动管理错误

### 决策 3：菜单 API 路径

**选择：** `/api/v1/menus/user`（通用业务接口）

**理由：**
- 菜单数据面向前端渲染，属于通用业务接口
- 不需要 `/admin/v1/` 管理端（CRUD 在后续变更）
- 不需要 `/inner/v1/` 内部接口（无跨模块调用需求）

### 决策 4：迁移重建策略

**选择：** 完全重建（DROP + CREATE）

**理由：**
- 当前为演示项目，无生产数据
- 避免复杂的表迁移脚本
- 确保表结构完全符合新的 schema 设计

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 迁移重建丢失现有数据 | 确认无生产数据后执行，种子数据可恢复基础数据 |
| 菜单-权限关联过于复杂 | 提供 `is_visible` 字段支持无条件显示的菜单 |
| 跨模块菜单跳转体验 | 前端使用子域名跳转，Cookie 共享（后续前端变更处理） |

## 迁移计划

### 步骤 1：修复 env.py 配置导入

```python
# 修复前
from demo.configs import settings

# 修复后
from framework.configs import get_settings
settings = get_settings()
```

### 步骤 2：重建 IAM 模块迁移

```bash
uv run python manage.py db rebuild --module iam
```

创建以下表在 `iam` schema：
- `users`、`roles`、`permissions`、`departments`
- `user_roles`、`role_permissions`、`user_tenants`、`user_departments`
- `oauth_connections`、`system_settings`、`system_setting_attributes`
- `menus`、`menu_permissions`（新增）

### 步骤 3：重建 Demo 模块迁移

```bash
uv run python manage.py db rebuild --module demo
```

创建以下表在 `demo` schema：
- `datasets`

### 步骤 4：初始化种子数据

```bash
uv run python manage.py seed --module iam
uv run python manage.py seed --module demo
```

种子数据包括：
- IAM：默认角色、权限、菜单
- Demo：示例数据集（如有）

## 待解决问题

无。
