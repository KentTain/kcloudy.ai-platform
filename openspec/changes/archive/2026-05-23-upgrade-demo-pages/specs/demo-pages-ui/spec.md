## ADDED Requirements

### Requirement: Demo 页面 AppPage 骨架

Demo 模块页面 SHALL 使用 AppPage 组件作为页面骨架替代独立容器 + CommonCard。

#### Scenario: HomePage AppPage 骨架

- **WHEN** HomePage 渲染
- **THEN** SHALL 使用 AppPage 组件，title 为 "欢迎使用 AI 助手平台"，variant 为 "list"

#### Scenario: HealthPage AppPage 骨架

- **WHEN** HealthPage 渲染
- **THEN** SHALL 使用 AppPage 组件，title 为 "健康检查"，variant 为 "list"

#### Scenario: DatasetsPage AppPage 骨架

- **WHEN** DatasetsPage 渲染
- **THEN** SHALL 使用 AppPage 组件，title 为 "知识库列表"，variant 为 "list"，actions slot 包含 "新建知识库" 按钮

### Requirement: HomePage shadcn Card 展示

HomePage SHALL 使用 shadcn Card 展示平台功能介绍卡片替代 CommonCard。

#### Scenario: 功能卡片展示

- **WHEN** HomePage 功能区域渲染
- **THEN** SHALL 使用 shadcn Card/CardHeader/CardContent 展示各功能模块（设计令牌系统、AdminLayout、UI 组件库、权限控制）

#### Scenario: 移除 CommonCard 依赖

- **WHEN** HomePage 组件导入声明
- **THEN** SHALL 不包含对 CommonCard 的引用

### Requirement: HealthPage shadcn Badge 状态标记

HealthPage SHALL 使用 shadcn Card + Badge 展示健康状态替代 CommonCard。

#### Scenario: 状态 Badge 展示

- **WHEN** 健康检查数据加载成功
- **THEN** SHALL 使用 Badge 组件展示状态，healthy 状态使用 variant="success"，unhealthy 状态使用 variant="destructive"

#### Scenario: 加载态 Skeleton

- **WHEN** 健康检查数据正在加载
- **THEN** SHALL 使用 Skeleton 组件做占位显示替代 CommonLoading

#### Scenario: 错误态重试

- **WHEN** 健康检查请求失败
- **THEN** SHALL 在 Card 内显示错误信息 + shadcn Button 重试按钮

#### Scenario: 移除 Common 组件依赖

- **WHEN** HealthPage 组件导入声明
- **THEN** SHALL 不包含对 CommonCard、CommonButton、CommonLoading 的引用

### Requirement: DatasetsPage shadcn Table 展示

DatasetsPage SHALL 使用 shadcn Table 展示数据集列表替代 CommonCard 内的简单列表。

#### Scenario: 表格列定义

- **WHEN** DatasetsPage 表格渲染
- **THEN** SHALL 展示以下列：名称、描述、状态（Badge）、创建时间、操作

#### Scenario: 搜索筛选

- **WHEN** DatasetsPage 筛选区域渲染
- **THEN** SHALL 提供 shadcn Input 搜索框，支持按名称筛选数据集

#### Scenario: 加载态 Skeleton

- **WHEN** 数据集数据正在加载
- **THEN** SHALL 使用 Skeleton 行级占位替代 CommonLoading

#### Scenario: 空态展示

- **WHEN** 数据集列表为空
- **THEN** SHALL 显示空数据提示文案

#### Scenario: 移除 Common 组件依赖

- **WHEN** DatasetsPage 组件导入声明
- **THEN** SHALL 不包含对 CommonCard、CommonButton、CommonLoading 的引用