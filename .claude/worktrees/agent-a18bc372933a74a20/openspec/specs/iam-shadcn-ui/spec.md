# iam-shadcn-ui Specification

## Purpose

定义 IAM 模块 shadcn 组件化 UI 规范，涵盖所有页面和树组件的 Element Plus → shadcn 迁移需求。

## Requirements

### Requirement: IAM 页面统一使用 AppPage 骨架

IAM 模块所有页面 SHALL 使用 AppPage 组件作为页面骨架替代 el-card 容器。

#### Scenario: 列表页 AppPage 骨架

- **WHEN** UserList/RoleList/TenantList/PermissionList 渲染
- **THEN** SHALL 使用 AppPage 组件（variant="list"），title 和 actions slot 配置页面标题和操作按钮

#### Scenario: 表单页 AppPage 骨架

- **WHEN** UserForm/RoleForm/TenantForm 渲染
- **THEN** SHALL 使用 AppPage 组件（variant="detail"），title 配置为 "创建用户"/"编辑角色" 等

#### Scenario: 详情页 AppPage 骨架

- **WHEN** UserDetail/TenantDetail 渲染
- **THEN** SHALL 使用 AppPage 组件（variant="detail"），title 和 actions slot 配置详情页标题和操作按钮

#### Scenario: 部门管理页 AppPage 骨架

- **WHEN** DepartmentPage 渲染
- **THEN** SHALL 使用 AppPage 组件（variant="workbench"），支持树 + 详情 + 用户列表的 workbench 布局

#### Scenario: Profile 页 AppPage 骨架

- **WHEN** Profile 渲染
- **THEN** SHALL 使用 AppPage 组件（variant="list"），title 为 "个人中心"

### Requirement: IAM 页面移除 Element Plus 依赖

IAM 模块所有页面和组件 SHALL 不包含对 Element Plus 组件（el-xxx）的引用。

#### Scenario: 页面文件无 el-xxx 导入

- **WHEN** IAM 模块页面/组件文件检查
- **THEN** SHALL 不包含 el-card、el-table、el-form、el-input、el-button、el-tag、el-select、el-pagination、el-tree、el-tabs、el-dialog、el-descriptions、el-date-picker、el-page-header、el-space、el-divider、el-checkbox、el-input-number、el-avatar、el-empty、v-loading 等任何 Element Plus 组件或指令

### Requirement: IAM 列表页 shadcn Table 展示

IAM 列表页 SHALL 使用 shadcn Table 替代 el-table。

#### Scenario: 表格列定义

- **WHEN** UserList/RoleList/TenantList 表格渲染
- **THEN** SHALL 使用 shadcn TableHeader/TableRow/TableHead/TableBody/TableCell 定义列

#### Scenario: 状态列 Badge 展示

- **WHEN** 列表页包含状态字段
- **THEN** SHALL 使用 Badge 替代 el-tag 展示状态（active → variant="success", inactive → variant="destructive", locked → variant="warning"）

### Requirement: IAM 表单 shadcn Form 校验

IAM 表单页 SHALL 使用 vee-validate + zod schema + shadcn FormField 替代 el-form + formRules。

#### Scenario: zod schema 定义

- **WHEN** 表单校验逻辑初始化
- **THEN** SHALL 定义 zod schema 包含各字段校验规则（required、min/max 长度、email 格式等）

#### Scenario: 表单提交校验

- **WHEN** 用户点击提交按钮
- **THEN** vee-validate SHALL 根据 zod schema 校验所有字段，校验失败时在 FormMessage 中显示错误提示

#### Scenario: 移除 el-form rules

- **WHEN** 表单页组件声明
- **THEN** SHALL 不包含 formRules 对象和 formRef.validate() 调用

### Requirement: IAM 加载态 Skeleton 替代

IAM 页面 SHALL 使用 Skeleton 替代 v-loading directive。

#### Scenario: 列表页加载态

- **WHEN** 列表页数据正在加载
- **THEN** SHALL 使用 Skeleton TableRow 行级占位替代 v-loading

#### Scenario: 详情页加载态

- **WHEN** 详情页数据正在加载
- **THEN** SHALL 使用 Skeleton 行占位替代 v-loading

### Requirement: IAM 搜索筛选区 shadcn 化

IAM 列表页搜索筛选区 SHALL 使用 shadcn Input/Select 替代 el-input/el-select。

#### Scenario: 搜索输入框

- **WHEN** 列表页搜索区域渲染
- **THEN** SHALL 使用 shadcn Input 替代 el-input

#### Scenario: 下拉筛选

- **WHEN** 列表页下拉筛选渲染
- **THEN** SHALL 使用 shadcn Select 替代 el-select + el-option

### Requirement: IAM 按钮 shadcn 化

IAM 页面所有操作按钮 SHALL 使用 shadcn Button 替代 el-button。

#### Scenario: 主操作按钮

- **WHEN** 创建/保存/提交按钮渲染
- **THEN** SHALL 使用 shadcn Button variant="default"

#### Scenario: 辅助操作按钮

- **WHEN** 编辑/删除/取消按钮渲染
- **THEN** SHALL 使用 shadcn Button variant="outline" 或 variant="ghost"

#### Scenario: 状态操作按钮

- **WHEN** 激活/停用按钮渲染
- **THEN** SHALL 使用 shadcn Button variant="destructive" 或 variant="outline"
