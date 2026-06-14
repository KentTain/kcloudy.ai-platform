## 为什么

当前 `Module`、`ModuleMenu`、`ModulePermission`、`ModuleRole` 存储在 `tenant` schema 中，但这些数据的定义权应该属于各业务模块。目前缺少让业务模块**声明式定义**自己元数据的机制，导致：

1. 数据需要手动管理或依赖分散的 seed 脚本
2. 前端菜单硬编码在 `AppNavMain.vue`，与后端定义脱节
3. 模块更新时无法自动同步元数据变更

现在做这个变更，是因为架构已经稳定，需要建立模块元数据的统一管理机制。

## 变更内容

1. **扩展 ModuleDescriptor 协议**：新增 `get_module_definition()` 方法，让业务模块声明自己的菜单、权限、默认角色
2. **新增模块定义同步服务**：应用启动时自动将模块声明同步到数据库，以模块定义为准
3. **新增用户菜单 API**：`GET /api/v1/user/menus` 返回当前用户有权限的菜单树
4. **改造前端菜单**：从 API 动态获取菜单，移除硬编码

## 功能 (Capabilities)

### 新增功能

- `module-metadata-declaration`: 模块元数据声明机制，扩展 ModuleDescriptor 协议，支持声明菜单、权限、默认角色
- `module-definition-sync`: 模块定义自动同步服务，应用启动时将模块声明同步到 tenant schema
- `user-menu-api`: 用户菜单 API，返回当前用户有权限访问的菜单树

### 修改功能

- `module-definition`: 新增模块声明式定义需求，模块创建时从声明同步而非手动管理
- `app-nav-main`: 改为从 API 动态获取菜单数据，支持 `items` prop 或从 store 获取
- `module-descriptor`: 前端 ModuleDescriptor 接口与后端协议对齐

## 影响

### 后端影响

| 文件/模块 | 变更类型 | 说明 |
|----------|---------|------|
| `framework/module/descriptor.py` | 修改 | 扩展协议，新增 `get_module_definition()` |
| `framework/module/definition.py` | 新增 | 定义 `ModuleDefinition`、`MenuDef`、`PermissionDef`、`RoleDef` 数据类 |
| `framework/module/sync_service.py` | 新增 | 模块定义同步服务 |
| `application_web.py` | 修改 | 启动时调用同步服务 |
| `iam/module.py` | 修改 | 实现 `get_module_definition()` |
| `tenant/module.py` | 修改 | 实现 `get_module_definition()` |
| `ai/module.py` | 修改 | 实现 `get_module_definition()` |
| `iam/controllers/user_menu_controller.py` | 新增 | 用户菜单 API |

### 前端影响

| 文件/模块 | 变更类型 | 说明 |
|----------|---------|------|
| `framework/layouts/components/AppNavMain.vue` | 修改 | 从 API/store 获取菜单 |
| `framework/stores/menu.ts` | 修改 | 新增从 API 获取菜单的方法 |
| `framework/api/menu.ts` | 新增 | 菜单 API 客户端 |
| `framework/module/types.ts` | 修改 | 扩展 ModuleDescriptor 类型 |

### 数据库影响

- 无 Schema 变更，复用现有 `modules`、`module_menus`、`module_permissions`、`module_roles` 表
- 同步策略为 upsert，基于 `code` 字段幂等操作

### 兼容性

- **向后兼容**：现有 API 不变，新增 `/api/v1/user/menus` 接口
- **迁移策略**：各模块逐步实现 `get_module_definition()`，未实现的模块保持手动管理
