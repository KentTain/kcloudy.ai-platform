## ADDED Requirements

### Requirement: Pagination 分页组件

系统 SHALL 提供自写 Pagination 组件替代 el-pagination，支持页码导航和每页条数切换。

#### Scenario: 页码导航

- **WHEN** 用户点击页码按钮
- **THEN** 组件 SHALL 触发 page-change 事件并传递新页码

#### Scenario: 每页条数切换

- **WHEN** 用户选择每页条数（10/20/50/100）
- **THEN** 组件 SHALL 触发 page-size-change 事件并传递新条数，页码重置为 1

#### Scenario: 总数显示

- **WHEN** Pagination 组件渲染
- **THEN** SHALL 显示总条数 "共 X 条"

#### Scenario: 边界条件

- **WHEN** 总条数为 0
- **THEN** 组件 SHALL 不显示分页控件

#### Scenario: 页码超出范围

- **WHEN** 当前页码大于最大页码
- **THEN** 组件 SHALL 自动修正为最后一页

### Requirement: Pagination 组件接口

Pagination 组件 SHALL 提供标准 Vue 组件接口。

#### Scenario: Props 定义

- **WHEN** 使用 Pagination 组件
- **THEN** SHALL 接受 props: total（总条数）、page（当前页码）、pageSize（每页条数）、pageSizeOptions（条数选项数组）

#### Scenario: Events 定义

- **WHEN** 页码或条数变化
- **THEN** SHALL 触发事件: update:page、update:pageSize

#### Scenario: 样式一致性

- **WHEN** Pagination 组件渲染
- **THEN** SHALL 使用 shadcn 设计令牌（bg-background, text-foreground, border-border 等），视觉风格与 shadcn Button 一致