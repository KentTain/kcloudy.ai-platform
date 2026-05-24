# common-tree-components

## Purpose

common-tree-components 提供一组通用树 UI 组件，包括基础展示树（CommonTree）、勾选树（CommonCheckboxTree）、下拉选择树（CommonSelectTree）和带操作按钮的列表树（CommonTreeList），用于前端树形数据的展示和交互。

## Requirements

### Requirement: CommonTree 基础展示树组件

`CommonTree.vue` SHALL 提供基础的树展示能力。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | TreeComponentNode[] | [] | 树数据 |
| defaultExpandLevel | number | 1 | 默认展开层级 |
| indent | number | 20 | 缩进像素 |
| nodeClass | string | "" | 节点样式类 |

#### Slots

| Slot | 参数 | 说明 |
|------|------|------|
| node | { node, level, isExpanded } | 完整节点插槽 |
| node-content | { node, level } | 节点内容插槽 |

#### Events

| Event | 参数 | 说明 |
|-------|------|------|
| node-click | { node, level } | 节点点击 |
| node-toggle | { node, isExpanded } | 展开/折叠 |

#### Scenario: 渲染树结构

- **WHEN** 传入树形数据
- **THEN** 正确渲染树结构，包含展开/折叠功能

#### Scenario: 默认展开层级

- **WHEN** 设置 defaultExpandLevel = 2
- **THEN** 前 2 层节点默认展开

#### Scenario: 节点点击事件

- **WHEN** 点击节点
- **THEN** 触发 node-click 事件

### Requirement: CommonCheckboxTree 勾选树组件

`CommonCheckboxTree.vue` SHALL 继承 CommonTree，增加勾选功能。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | (string | number)[] | [] | 选中的节点ID |
| disabled | boolean | false | 禁用状态 |
| searchable | boolean | true | 是否可搜索 |
| placeholder | string | "搜索..." | 搜索框占位符 |

#### Scenario: 单选模式

- **WHEN** 选中一个节点
- **THEN** modelValue 更新为该节点ID

#### Scenario: 多选模式

- **WHEN** 选中父节点
- **THEN** 所有子孙叶子节点被选中

#### Scenario: 半选状态

- **WHEN** 部分子节点被选中
- **THEN** 父节点显示半选状态（indeterminate）

#### Scenario: 搜索过滤

- **WHEN** 输入搜索关键词
- **THEN** 仅显示匹配节点及其祖先节点

### Requirement: CommonSelectTree 下拉选择树组件

`CommonSelectTree.vue` SHALL 提供下拉弹层选择树功能。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | string | string[] | "" | 选中的值 |
| mode | "single" | "multiple" | "single" | 选择模式 |
| placeholder | string | "请选择" | 输入框占位符 |
| disabled | boolean | false | 禁用状态 |

#### Scenario: 单选下拉

- **WHEN** mode = "single" 且选中节点
- **THEN** 输入框显示节点名称
- **THEN** modelValue 更新为节点ID

#### Scenario: 多选下拉

- **WHEN** mode = "multiple" 且选中多个节点
- **THEN** 输入框显示多个标签
- **THEN** modelValue 更新为节点ID数组

#### Scenario: 下拉展开

- **WHEN** 点击输入框
- **THEN** 弹出树形选择面板

### Requirement: CommonTreeList 列表树组件

`CommonTreeList.vue` SHALL 提供带操作按钮的列表树。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | TreeComponentNode[] | [] | 树数据 |
| actions | TreeAction[] | [] | 操作按钮配置 |

#### TreeAction

```typescript
interface TreeAction {
  key: string;
  label: string;
  icon?: Component;
  visible?: (node: TreeComponentNode) => boolean;
  handler: (node: TreeComponentNode) => void;
}
```

#### Scenario: 渲染操作按钮

- **WHEN** 配置 actions
- **THEN** 每个节点右侧显示操作按钮

#### Scenario: 条件显示按钮

- **WHEN** action.visible 返回 false
- **THEN** 该按钮不显示

#### Scenario: 按钮点击

- **WHEN** 点击操作按钮
- **THEN** 触发对应的 handler