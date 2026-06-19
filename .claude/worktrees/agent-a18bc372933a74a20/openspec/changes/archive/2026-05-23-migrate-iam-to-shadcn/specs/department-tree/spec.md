## MODIFIED Requirements

### Requirement: 部门选择

系统 SHALL 支持部门节点选择功能，DepartmentTree SHALL 使用 CheckboxTree 替代 el-tree。

#### Scenario: 单选模式
- **WHEN** 组件设置为单选模式
- **THEN** 用户只能选择一个部门节点，CheckboxTree SHALL 支持 singleSelect 模式

#### Scenario: 多选模式
- **WHEN** 组件设置为多选模式
- **THEN** 用户可以选择多个部门节点，CheckboxTree SHALL 支持勾选模式

#### Scenario: 选择事件
- **WHEN** 用户点击选择部门节点
- **THEN** 组件 SHALL 触发 node-click 事件传递选中节点数据

### Requirement: 部门搜索

系统 SHALL 支持搜索过滤部门，搜索框 SHALL 使用 shadcn Input 替代 el-input。

#### Scenario: 按名称搜索
- **WHEN** 用户在搜索框输入部门名称关键字
- **THEN** CheckboxTree SHALL 过滤并高亮匹配的部门节点

#### Scenario: 搜索结果定位
- **WHEN** 搜索有匹配结果
- **THEN** CheckboxTree SHALL 自动展开并定位到匹配节点