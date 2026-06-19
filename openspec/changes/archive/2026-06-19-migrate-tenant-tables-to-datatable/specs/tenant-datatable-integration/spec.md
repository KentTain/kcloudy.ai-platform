# tenant-datatable-integration 规格

## 概述

Tenant 模块列表页面集成通用 DataTable 组件，实现标准化的数据展示、分页和加载状态管理。

## 新增需求

### 需求:TenantList 使用 DataTable

TenantList 页面必须使用 DataTable 组件替代原生 Table 组件，通过 useDataTable 管理列表状态。

#### 场景:租户列表正常展示

- **当** 用户访问 `/tenants` 页面
- **那么** 系统使用 DataTable 组件展示租户列表
- **那么** DataTable 自动处理分页、加载状态和空状态

#### 场景:租户列表搜索筛选

- **当** 用户输入搜索关键字并点击搜索按钮
- **那么** 系统调用 `dataTable.refresh(true)` 重新加载数据
- **那么** 搜索参数传递给 API 请求

### 需求:ModuleList 使用 DataTable

ModuleList 页面必须使用 DataTable 组件替代原生 Table 组件，支持模块列表的标准展示。

#### 场景:模块列表正常展示

- **当** 用户访问 `/admin/modules` 页面
- **那么** 系统使用 DataTable 组件展示模块列表
- **那么** 表格列包括：模块信息、状态、必须模块、分配次数、创建时间、操作

### 需求:ResourceConfigList 使用 DataTable

ResourceConfigList 页面的 5 个资源类型 Tab 必须各自使用独立的 DataTable 实例。

#### 场景:资源配置 Tab 切换

- **当** 用户切换资源类型 Tab（数据库/存储/缓存/队列/发布订阅）
- **那么** 当前 Tab 的 DataTable 自动加载数据
- **那么** 非活动 Tab 的 DataTable 不发送请求（通过 `enabled` 条件控制）

#### 场景:资源配置列表搜索

- **当** 用户在搜索框输入关键字
- **那么** 系统刷新所有 Tab 的 DataTable 数据

### 需求:列定义配置化

表格列定义必须使用 ColumnDef 配置，支持自定义单元格渲染。

#### 场景:操作按钮列定义

- **当** 定义操作列
- **那么** 使用 `cell` 渲染函数返回操作按钮组件
- **那么** 按钮包括：详情、编辑、删除、激活/停用等操作

### 需求:API 类型声明更新

Tenant 模块 API 函数必须使用 `SuccessExtra<T[]>` 作为返回类型声明。

#### 场景:getTenants 返回类型

- **当** 调用 `getTenants()` 函数
- **那么** 返回类型声明为 `SuccessExtra<Tenant[]>`
- **那么** 返回数据结构为 `{ code, msg, data: Tenant[], total, page, page_size }`

#### 场景:getModules 返回类型

- **当** 调用 `getModules()` 函数
- **那么** 返回类型声明为 `SuccessExtra<Module[]>`

#### 场景:getDatabaseConfigs 返回类型

- **当** 调用 `getDatabaseConfigs()` 函数
- **那么** 返回类型声明为 `SuccessExtra<DatabaseConfig[]>`

## 验收标准

- [ ] TenantList.vue 使用 DataTable 组件
- [ ] ModuleList.vue 使用 DataTable 组件
- [ ] ResourceConfigList.vue 5 个 Tab 各使用独立 DataTable
- [ ] API 类型声明使用 `SuccessExtra<T[]>`
- [ ] 搜索筛选功能正常
- [ ] 分页功能正常
- [ ] 骨架屏加载状态正常
- [ ] 空状态展示正常
