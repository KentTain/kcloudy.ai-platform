# theme-switching Specification

## Purpose
TBD - created by archiving change enhance-admin-shell-ui. Update Purpose after archive.
## Requirements
### Requirement: Theme switching
系统 SHALL 提供亮色、暗色、跟随系统三种主题模式，用户可以在 SidebarFooter 用户菜单中切换。

#### Scenario: Switch to dark mode
- **WHEN** 用户在 SidebarFooter 下拉菜单中选择"切换主题 → 暗色"
- **THEN** 系统将主题设为 `dark`，页面背景变为暗色，文字变为亮色

#### Scenario: Switch to light mode
- **WHEN** 用户在 SidebarFooter 下拉菜单中选择"切换主题 → 亮色"
- **THEN** 系统将主题设为 `light`，页面背景变为亮色，文字变为暗色

#### Scenario: Follow system preference
- **WHEN** 用户在 SidebarFooter 下拉菜单中选择"切换主题 → 跟随系统"
- **THEN** 系统将主题设为 `auto`，根据操作系统偏好自动切换亮色或暗色

#### Scenario: Persist theme preference
- **WHEN** 用户切换主题后刷新页面或重新访问
- **THEN** 系统从 localStorage 恢复上次选择的主题模式

#### Scenario: Default theme on first visit
- **WHEN** 用户首次访问系统且无 localStorage 中的主题偏好
- **THEN** 系统默认使用 `light` 主题

