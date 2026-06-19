## ADDED Requirements

### Requirement: DescriptionList 组件

系统 SHALL 提供自写 DescriptionList 组件替代 el-descriptions，支持 key-value 对齐展示。

#### Scenario: 基本渲染

- **WHEN** DescriptionList 接收 items 数组（label + value）
- **THEN** SHALL 使用 grid 布局对齐展示每项的 label 和 value

#### Scenario: 多列布局

- **WHEN** 设置 columns prop 为 2 或 3
- **THEN** SHALL 每行展示对应数量的 label-value 对

#### Scenario: 空值处理

- **WHEN** value 为空或 undefined
- **THEN** SHALL 显示占位符 "--"

#### Scenario: 值类型渲染

- **WHEN** value 为 Badge/status 类型
- **THEN** SHALL 渲染 Badge 组件而非纯文本

#### Scenario: Border 样式

- **WHEN** 设置 bordered prop 为 true
- **THEN** SHALL 在 label 和 value 之间显示分隔线

### Requirement: DescriptionList 组件接口

DescriptionList SHALL 提供标准 Vue 组件接口。

#### Scenario: Props 定义

- **WHEN** 使用 DescriptionList 组件
- **THEN** SHALL 接受 props: items（label/value/badgeVariant 数组）、columns（列数）、bordered（是否带边框）

#### Scenario: Slot 支持

- **WHEN** 需要自定义 value 渲染
- **THEN** SHALL 支持 item slot，传入 item 数据供自定义渲染