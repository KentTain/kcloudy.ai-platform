# iam-checkbox-tree Specification

## Purpose

定义 IAM 模块递归树组件规范，替代 el-tree，支持勾选/半选/搜索/展开折叠。

## Requirements

### Requirement: CheckboxTree 递归树组件

系统 SHALL 提供自写 CheckboxTree 组件替代 el-tree，支持勾选/半选/搜索/展开折叠。

#### Scenario: 递归渲染树节点

- **WHEN** CheckboxTree 接收 TreeNode 数据（含 children）
- **THEN** SHALL 递归渲染树形结构，每节点显示展开图标 + 名称 + 勾选框

#### Scenario: 勾选功能

- **WHEN** 用户勾选叶子节点
- **THEN** 该节点 SHALL 被添加到已选列表，父节点显示半选（indeterminate）状态

#### Scenario: 全选子节点

- **WHEN** 用户勾选父节点
- **THEN** SHALL 自动勾选该父节点下所有子节点

#### Scenario: 取消全选子节点

- **WHEN** 用户取消勾选父节点
- **THEN** SHALL 自动取消勾选该父节点下所有子节点

#### Scenario: 半选状态取消

- **WHEN** 父节点处于半选状态且用户勾选该父节点
- **THEN** SHALL 变为全选状态（所有子节点被勾选）

### Requirement: CheckboxTree 搜索过滤

CheckboxTree SHALL 支持搜索过滤树节点。

#### Scenario: 搜索匹配节点

- **WHEN** 用户在搜索框输入关键字
- **THEN** SHALL 仅显示名称包含关键字的节点及其祖先路径

#### Scenario: 搜索无匹配

- **WHEN** 搜索关键字无匹配节点
- **THEN** SHALL 显示空状态提示

### Requirement: CheckboxTree 组件接口

CheckboxTree SHALL 提供标准 Vue 组件接口。

#### Scenario: v-model 绑定

- **WHEN** 使用 CheckboxTree 组件绑定 v-model
- **THEN** 已选节点 ID 列表 SHALL 与绑定值同步

#### Scenario: 数据传入

- **WHEN** 通过 data prop 传入 TreeNode 数组
- **THEN** SHALL 渲染对应的树结构

#### Scenario: 禁用状态

- **WHEN** 设置 disabled prop 为 true
- **THEN** SHALL 禁止勾选/取消勾选操作

#### Scenario: 默认展开层级

- **WHEN** 设置 defaultExpandLevel prop
- **THEN** SHALL 默认展开到指定层级
