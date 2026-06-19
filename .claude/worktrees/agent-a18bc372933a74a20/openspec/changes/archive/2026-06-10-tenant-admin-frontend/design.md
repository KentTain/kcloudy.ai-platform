# 租户管理前端功能设计

## 上下文

### 当前状态

后端 `tenant-module-system` 变更已完成以下 API 实现：
- 租户管理 API (`/admin/v1/tenants/*`)
- 资源配置 API (`/admin/v1/resource-configs/*`)
- 模块管理 API (`/admin/v1/modules/*`)
- 租户模块分配 API (`/admin/v1/tenants/{id}/modules/*`)

前端 `migrate-common-components` 变更已完成通用组件迁移：
- `DataTable`：基于 @tanstack/vue-table 的高级表格
- `MessageBox`：服务式消息框
- `SmartTooltip`：智能溢出提示
- `Tree`：基础树组件

### 参考项目

Alon 项目的 `system/` 目录提供了系统管理页面的参考实现：
- 统计卡片 + 数据表格 + 弹窗表单的布局模式
- 使用 `AlonDataTable` 展示数据
- 使用 `Dialog` 进行创建/编辑操作
- 使用 `AlertDialog` 进行删除确认

### 约束

- 仅实现需求文档描述的功能，不自行扩展
- 复用已迁移的通用组件
- 遵循 Vue 3 + TypeScript + shadcn-vue 技术栈

## 目标 / 非目标

**目标：**

1. 实现资源配置管理页面，支持 5 种资源类型的 CRUD 和连通性测试
2. 实现模块管理页面，包含模块、菜单、权限、角色的管理
3. 扩展租户详情页，支持资源绑定和模块分配
4. 提供统一的用户体验，参照 Alon 项目风格

**非目标：**

1. 不实现统计数据的后端 API（使用现有数据推算统计值）
2. 不实现租户实例层的菜单/权限/角色查询（属于 IAM 模块范围）
3. 不实现密码加密相关的前端逻辑（后端已处理）

## 决策

### 1. 页面组织结构

**决策**：采用 Tab 切换的统一页面结构

**理由**：
- 资源配置 5 种类型结构相似，Tab 切换减少页面跳转
- 模块详情包含 4 个子功能（基本信息/菜单/权限/角色），Tab 切换保持上下文
- 租户详情扩展为 Tab 结构，与现有页面风格一致

**页面结构**：

```
/admin
├── /tenants                           租户列表（更新）
│   ├── /create                        创建租户
│   └── /:id                           租户详情（扩展 Tab）
│       ├── Tab: 基本信息
│       ├── Tab: 资源绑定
│       └── Tab: 模块分配
│
├── /resource-configs                  资源配置管理（新建）
│   ├── Tab: 数据库
│   ├── Tab: 存储
│   ├── Tab: 缓存
│   ├── Tab: 队列
│   └── Tab: 发布订阅
│
└── /modules                           模块管理（新建）
    ├── /create                        创建模块
    └── /:id                           模块详情
        ├── Tab: 基本信息
        ├── Tab: 菜单管理
        ├── Tab: 权限管理
        └── Tab: 角色管理
```

### 2. 组件选型

**决策**：复用已迁移的通用组件

| 组件 | 来源 | 用途 |
|------|------|------|
| DataTable | `@/components/common/data-display/table/` | 数据表格 |
| Dialog | `@/components/ui/dialog/` | 弹窗表单 |
| AlertDialog | `@/components/ui/alert-dialog/` | 删除确认 |
| Tabs | `@/components/ui/tabs/` | Tab 切换 |
| Tree | `@/components/ui/tree/` | 菜单树展示 |
| Card | `@/components/ui/card/` | 统计卡片 |
| Badge | `@/components/ui/badge/` | 状态标签 |
| Input, Select, Label | `@/components/ui/` | 表单控件 |

**理由**：
- 保持组件一致性
- 减少重复开发
- 符合项目架构规范

### 3. 菜单编辑交互

**决策**：采用弹窗表单方式编辑菜单

**理由**：
- 与 Alon 角色管理页面风格一致
- 实现简单，交互统一
- 父菜单通过 TreeSelect 选择

**交互流程**：
1. 点击「新增菜单」弹出 Dialog
2. 表单包含：菜单名称、编码、路径、父菜单（下拉选择）、图标、排序
3. 提交后刷新菜单树

### 4. 统计卡片数据来源

**决策**：从列表数据推算统计值

**统计项**：
- **资源配置页面**：配置总数、已被引用、未被使用
- **模块管理页面**：模块总数、启用模块、必须模块、已分配次数

**实现方式**：
- 配置总数：列表数据长度
- 已被引用：列表数据中 `tenant_count > 0` 的数量
- 启用模块：列表数据中 `is_active = true` 的数量
- 必须模块：列表数据中 `is_need = true` 的数量
- 已分配次数：需要额外调用模块分配统计 API 或从租户模块列表获取

### 5. API 模块结构

**决策**：按功能域划分 API 模块

```
web/vue/src/tenant/api/
├── admin.ts           # 管理员认证 API（已存在）
├── tenant.ts          # 租户管理 API（已存在）
├── resourceConfig.ts  # 资源配置 API（新建）
├── module.ts          # 模块管理 API（新建）
└── tenantModule.ts    # 租户模块分配 API（新建）
```

**API 函数设计**：

```typescript
// resourceConfig.ts
export const databaseConfigApi = {
  list: (params: ListQuery) => apiClient.get('/admin/v1/resource-configs/databases', { params }),
  get: (id: string) => apiClient.get(`/admin/v1/resource-configs/databases/${id}`),
  create: (data: DatabaseConfigCreate) => apiClient.post('/admin/v1/resource-configs/databases', data),
  update: (id: string, data: DatabaseConfigUpdate) => apiClient.put(`/admin/v1/resource-configs/databases/${id}`, data),
  delete: (id: string) => apiClient.delete(`/admin/v1/resource-configs/databases/${id}`),
  testConnection: (id: string) => apiClient.post(`/admin/v1/resource-configs/databases/${id}/test-connection`),
};

// 其他 4 种资源配置 API 结构相同
```

## 风险 / 权衡

### 风险 1：统计卡片数据准确性

**风险**：分页查询时，统计值可能不准确

**缓解措施**：
- 列表查询时使用较大的 page_size（如 100）获取完整数据
- 或后端提供独立的统计 API（后续优化）

### 风险 2：菜单树编辑的父子关系验证

**风险**：编辑菜单时选择父菜单可能导致循环引用

**缓解措施**：
- 前端过滤当前菜单及其子菜单，不允许选为父菜单
- 后端已有验证逻辑，前端辅助提升用户体验

### 风险 3：模块删除的级联影响

**风险**：删除已分配模块会影响租户

**缓解措施**：
- 前端显示确认对话框，提示模块分配情况
- 后端已有校验逻辑，禁止删除已分配模块

## 迁移计划

### 阶段 1：API 模块和类型定义

1. 创建 `types/resource.ts` 资源配置类型
2. 创建 `types/module.ts` 扩展模块管理类型
3. 创建 `api/resourceConfig.ts` 资源配置 API
4. 创建 `api/module.ts` 模块管理 API
5. 创建 `api/tenantModule.ts` 租户模块分配 API

### 阶段 2：资源配置管理页面

1. 创建 `pages/admin/ResourceConfigList.vue`
2. 创建 `components/ResourceConfigForm.vue` 表单弹窗

### 阶段 3：模块管理页面

1. 创建 `pages/admin/ModuleList.vue`
2. 创建 `pages/admin/ModuleDetail.vue`
3. 创建 `pages/admin/ModuleForm.vue`
4. 创建模块菜单/权限/角色相关组件

### 阶段 4：租户详情页扩展

1. 更新 `pages/tenants/TenantDetail.vue` 为 Tab 结构
2. 创建资源绑定 Tab 组件
3. 创建模块分配 Tab 组件

### 阶段 5：路由配置

1. 更新 `router/index.ts` 添加新路由

### 阶段 6：验证

1. 运行构建验证
2. 运行类型检查
3. 运行测试验证
