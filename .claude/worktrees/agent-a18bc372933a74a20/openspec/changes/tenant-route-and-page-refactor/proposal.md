# Tenant 模块路由与页面重构

## 为什么

当前资源配置管理的 API 路由使用 `/admin/resource-configs`，路径较长且与其他模块路由风格不一致。同时，租户管理页面缺少统计信息展示，用户体验有待优化。

此次变更将：
1. 统一 API 路由风格，将 `resource-configs` 简化为 `resources`
2. 优化租户管理页面，添加统计卡片区域，提升用户决策效率

## 变更内容

### 路由变更

**后端 API 路由**
- `/tenant/admin/v1/resource-configs/databases` → `/tenant/admin/v1/resources/databases`
- `/tenant/admin/v1/resource-configs/storages` → `/tenant/admin/v1/resources/storages`
- `/tenant/admin/v1/resource-configs/caches` → `/tenant/admin/v1/resources/caches`
- `/tenant/admin/v1/resource-configs/queues` → `/tenant/admin/v1/resources/queues`
- `/tenant/admin/v1/resource-configs/pubsubs` → `/tenant/admin/v1/resources/pubsubs`

**前端路由**
- `/admin/resource-configs` → `/admin/resources`

**菜单数据**
- `tenant.module_menus` 表：更新 `tenant.resources` 菜单的 `path` 字段
- `iam.menus` 表：更新 `tenant.resources` 菜单的 `path` 字段

### 页面重构

**TenantList 页面优化**
- 新增统计卡片区，展示关键指标：
  - 租户总数
  - 未激活租户数
  - 过期租户数
- 参照 `ModuleList.vue` 的布局风格
- 保留 `AppPage` 组件，仅添加统计区域

### 数据迁移

创建数据库迁移脚本 `007_update_menu_paths_to_resources.py`，自动更新已存在的菜单数据。

## 功能 (Capabilities)

### 新增功能

- `tenant-statistics`: 租户统计功能，提供租户总数、未激活数、过期数的实时统计

### 修改功能

- `tenant-resource-management`: 资源配置管理功能，API 路由从 `resource-configs` 变更为 `resources`（**BREAKING** - 接口路径变更，需同步更新前端调用）

## 影响

### 后端影响

- **Controller**: `tenant/controllers/admin/resource_config_controller.py` - 5 个路由前缀常量
- **Module**: `tenant/module.py` - MenuDef 的 path 字段
- **Service**: `tenant/services/tenant_service.py` - 新增统计查询方法
- **Migration**: 新建迁移脚本更新菜单路径
- **API**: 破坏性变更，所有资源配置 API 路径变更

### 前端影响

- **API 层**: `tenant/api/resourceConfig.ts` - 25 个 API 函数路径
- **路由**: `tenant/router/index.ts` - 路由配置
- **页面**: `tenant/pages/tenants/TenantList.vue` - 添加统计卡片区域
- **组件**: 新增统计卡片组件（可复用）

### 数据库影响

- `tenant.module_menus` 表：更新 1 条记录（`tenant.resources` 菜单）
- `iam.menus` 表：更新 1 条记录（`tenant.resources` 菜单）

### 兼容性考虑

- **BREAKING**: API 路径变更，需确保前端同步更新
- 数据迁移脚本支持回滚（downgrade）
- 菜单数据迁移需在部署时执行
