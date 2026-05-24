# menu-permission-filter Specification

## Purpose
TBD - created by archiving change enhance-admin-shell-ui. Update Purpose after archive.
## Requirements
### Requirement: Dynamic menu filtering by permission
系统 SHALL 根据当前用户的权限动态过滤 Sidebar 菜单项，仅显示用户有权访问的页面入口。

#### Scenario: Show all menus when no permission config
- **WHEN** 权限配置未设置或为空
- **THEN** 系统显示所有菜单项（默认行为，向后兼容）

#### Scenario: Filter menus by user permission
- **WHEN** 用户拥有 `iam.users` 和 `iam.roles` 权限但缺少 `iam.departments` 权限
- **THEN** Sidebar 仅显示"用户管理"和"角色管理"菜单项，隐藏"部门管理"

#### Scenario: Hide entire group when all items filtered
- **WHEN** 一个菜单分组中的所有子项都被权限过滤掉
- **THEN** 系统隐藏整个分组（包括分组标题）

#### Scenario: Update menu on permission change
- **WHEN** 用户权限发生变化（如角色切换后）
- **THEN** 菜单项立即更新，反映新的权限范围

### Requirement: Permission key matching
菜单权限过滤 SHALL 支持层级权限键匹配，父级权限键可以覆盖子级。

#### Scenario: Parent key covers children
- **WHEN** 用户拥有 `iam` 权限键
- **THEN** 系统显示所有 `iam.*` 子权限对应的菜单项（如 `iam.users`、`iam.roles` 等）

#### Scenario: Specific key does not cover siblings
- **WHEN** 用户仅拥有 `iam.users` 权限键
- **THEN** 系统仅显示"用户管理"菜单项，不显示"角色管理"等其他 IAM 菜单

