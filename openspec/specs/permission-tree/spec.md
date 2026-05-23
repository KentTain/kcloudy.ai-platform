# permission-tree Specification

## Purpose

定义权限树组件，用于角色管理中的权限分配。支持按资源分组的树形结构展示权限，方便用户批量选择和分配权限。

## Requirements

### Requirement: 树形权限展示

系统 SHALL 支持按资源分组的树形结构展示权限。

#### Scenario: 按资源分组

- **WHEN** 组件加载权限数据
- **THEN** 权限按资源分组，资源作为父节点，权限作为子节点

#### Scenario: 展示权限信息

- **WHEN** 用户展开某个资源节点
- **THEN** 系统展示该资源下的所有权限，包括权限名称、编码和描述

### Requirement: 权限选择

系统 SHALL 支持多选权限功能。

#### Scenario: 勾选权限

- **WHEN** 用户勾选某个权限
- **THEN** 该权限被添加到已选权限列表

#### Scenario: 勾选资源节点

- **WHEN** 用户勾选某个资源节点
- **THEN** 该资源下的所有权限被选中

#### Scenario: 取消勾选

- **WHEN** 用户取消勾选某个权限或资源节点
- **THEN** 对应权限从已选列表移除

### Requirement: 权限搜索

系统 SHALL 支持搜索过滤权限。

#### Scenario: 按名称搜索

- **WHEN** 用户在搜索框输入权限名称关键字
- **THEN** 系统过滤并展示匹配的权限及其父节点

#### Scenario: 无匹配结果

- **WHEN** 搜索关键字无匹配结果
- **THEN** 系统展示空状态提示

### Requirement: 组件接口

系统 SHALL 提供权限树组件的标准接口。

#### Scenario: v-model 绑定

- **WHEN** 使用组件时绑定 v-model
- **THEN** 组件选中状态与绑定值同步

#### Scenario: 权限数据传入

- **WHEN** 通过 permissions prop 传入权限列表
- **THEN** 组件渲染对应的权限树

#### Scenario: 禁用状态

- **WHEN** 设置 disabled prop 为 true
- **THEN** 组件处于只读状态，无法修改选择
