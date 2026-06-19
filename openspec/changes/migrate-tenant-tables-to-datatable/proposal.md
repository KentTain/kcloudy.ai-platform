## 为什么

Tenant 模块的三个列表页面（TenantList、ModuleList、ResourceConfigList）当前使用原生 Table 组件，存在大量重复代码：手动分页管理、骨架屏实现、空状态处理、请求取消逻辑。项目已有通用 DataTable 组件（基于 @tanstack/vue-table），提供开箱即用的分页、加载状态、空状态和请求取消能力。迁移到 DataTable 可减少约 60% 的模板代码，提升可维护性。

## 变更内容

- **前端类型更新**：`ApiResponse.message` → `msg`，新增 `SuccessExtra` 类型与后端响应格式对齐
- **API 类型声明**：更新 tenant API 返回类型为 `SuccessExtra<T[]>`
- **TenantList 迁移**：原生 Table + 手动分页 → DataTable 组件
- **ModuleList 迁移**：原生 Table + 手动分页 → DataTable 组件
- **ResourceConfigList 迁移**：5 个 Tab 的原生 Table + 手动分页 → DataTable 组件

## 功能 (Capabilities)

### 新增功能

- `tenant-datatable-integration`: Tenant 模块集成通用 DataTable 组件，实现列表页面的标准化展示

### 修改功能

- `framework-types`: 前端类型定义更新，`ApiResponse.message` 改为 `msg`，新增 `SuccessExtra` 类型

## 影响

### 代码影响

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `web/vue/src/framework/types/index.ts` | 修改 | 类型定义更新 |
| `web/vue/src/tenant/api/tenant.ts` | 修改 | 返回类型声明 |
| `web/vue/src/tenant/api/module.ts` | 修改 | 返回类型声明 |
| `web/vue/src/tenant/api/resourceConfig.ts` | 修改 | 返回类型声明 |
| `web/vue/src/tenant/pages/tenants/TenantList.vue` | 重构 | 迁移到 DataTable |
| `web/vue/src/tenant/pages/admin/ModuleList.vue` | 重构 | 迁移到 DataTable |
| `web/vue/src/tenant/pages/admin/ResourceConfigList.vue` | 重构 | 迁移到 DataTable |

### API 兼容性

- 后端已使用 `SuccessExtra` 响应类，格式完全兼容
- 无 API 变更，仅前端类型声明调整

### 依赖影响

- 无新增依赖
- DataTable 和 useDataTable 已存在于 `@/components`
