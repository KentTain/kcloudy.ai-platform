# common-tree-components

## Purpose

common-tree-components 提供一组通用树 UI 组件，包括基础展示树（CommonTree）、勾选树（CommonCheckboxTree）、下拉选择树（CommonSelectTree）和带操作按钮的列表树（CommonTreeList），用于前端树形数据的展示和交互。
## Requirements
### 需求: CommonTree 基础展示树组件

`CommonTree.vue` SHALL 提供基础的树展示能力，增强支持 checkbox 和异步加载。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | TreeSelectNode[] | [] | 树数据（类型变更） |
| checkable | boolean | false | **新增** 显示复选框 |
| cascade | boolean | false | **新增** 级联选择 |
| modelValue | (string \| number)[] | [] | **新增** 选中的节点 ID |
| multiple | boolean | false | **新增** 多选模式 |
| loadData | (node, callback) => void | - | **新增** 异步加载子节点 |
| defaultExpandLevel | number | 1 | 默认展开层级 |
| indent | number | 20 | 缩进像素 |
| showLine | boolean | false | **新增** 显示连接线 |
| disabled | boolean | false | **新增** 禁用状态 |
| nodeClass | string | "" | 节点样式类 |

#### Events

| Event | 参数 | 说明 |
|-------|------|------|
| node-click | { node, level } | 节点点击 |
| node-toggle | { node, isExpanded } | 展开/折叠 |
| update:modelValue | (string \| number)[] | **新增** 选中值变化 |

#### 场景:渲染树结构
- **当** 传入树形数据
- **那么** 正确渲染树结构，包含展开/折叠功能

#### 场景:复选框选择
- **当** checkable = true 且点击节点复选框
- **那么** 触发 update:modelValue 事件

#### 场景:级联选择
- **当** cascade = true 且选中父节点
- **那么** 所有子孙节点被选中

#### 场景:异步加载
- **当** 提供 loadData 且展开非叶子节点
- **那么** 调用 loadData 加载子节点

### 需求: CommonCheckboxTree 勾选树组件

`CommonCheckboxTree.vue` SHALL 使用 useTreeData 重构，提供勾选功能。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | TreeSelectNode[] | [] | 树数据（类型变更） |
| modelValue | (string \| number)[] | [] | 选中的节点ID |
| disabled | boolean | false | 禁用状态 |
| searchable | boolean | true | 是否可搜索 |
| placeholder | string | "搜索..." | 搜索框占位符 |

#### 场景:单选模式
- **当** 选中一个节点
- **那么** modelValue 更新为该节点ID

#### 场景:多选模式
- **当** 选中父节点
- **那么** 所有子孙叶子节点被选中

#### 场景:半选状态
- **当** 部分子节点被选中
- **那么** 父节点显示半选状态（indeterminate）

#### 场景:搜索过滤
- **当** 输入搜索关键词
- **那么** 仅显示匹配节点及其祖先节点

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

### 需求: CommonTreeList 列表树组件

`CommonTreeList.vue` SHALL 提供带操作按钮的列表树。

#### Props

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | TreeSelectNode[] | [] | 树数据（类型变更） |
| actions | TreeAction[] | [] | 操作按钮配置 |

#### TreeAction

```typescript
interface TreeAction {
  key: string;
  label: string;
  icon?: Component;
  visible?: (node: TreeSelectNode) => boolean;
  handler: (node: TreeSelectNode) => void;
}
```

#### 场景:渲染操作按钮
- **当** 配置 actions
- **那么** 每个节点右侧显示操作按钮

#### 场景:条件显示按钮
- **当** action.visible 返回 false
- **那么** 该按钮不显示

### 需求:组件支持多种数据格式输入

Tree 组件必须支持接收 TreeNode 或 TreeSelectNode 格式的数据，内部统一处理转换。

#### 场景:接收 TreeNode 格式数据
- **当** 传入 TreeNode[] 数据
- **那么** 组件正确渲染树结构

#### 场景:接收 TreeSelectNode 格式数据
- **当** 传入 TreeSelectNode[] 数据
- **那么** 组件正确渲染树结构

