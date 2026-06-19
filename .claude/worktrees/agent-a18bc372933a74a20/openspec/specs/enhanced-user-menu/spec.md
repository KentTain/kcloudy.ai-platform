# enhanced-user-menu Specification

## Purpose
TBD - created by archiving change enhance-admin-shell-ui. Update Purpose after archive.
## Requirements
### Requirement: User menu with settings entries
系统 SHALL 在 SidebarFooter 提供增强的用户下拉菜单，包含账号设置、开发者设置和主题切换入口。

#### Scenario: Open user dropdown menu
- **WHEN** 用户点击 SidebarFooter 中的用户头像/名称区域
- **THEN** 系统展开下拉菜单，显示用户信息、主题切换、账号设置、开发者设置和退出登录选项

#### Scenario: Navigate to account settings
- **WHEN** 用户在下拉菜单中点击"账号设置"
- **THEN** 系统跳转至 `/settings/account` 页面

#### Scenario: Navigate to developer settings
- **WHEN** 用户在下拉菜单中点击"开发者设置"
- **THEN** 系统跳转至 `/settings/developer` 页面

#### Scenario: Toggle theme from menu
- **WHEN** 用户在下拉菜单中点击"切换主题"
- **THEN** 系统切换当前主题模式（亮色 → 暗色，暗色 → 亮色）

#### Scenario: Logout from menu
- **WHEN** 用户在下拉菜单中点击"退出登录"
- **THEN** 系统清除登录状态并跳转至登录页面

### Requirement: User info display in footer
SidebarFooter SHALL 展示当前用户的头像（或首字母）、昵称和用户名。

#### Scenario: Display user with avatar
- **WHEN** 用户已登录且拥有头像 URL
- **THEN** SidebarFooter 显示用户头像图片、昵称和用户名

#### Scenario: Display user without avatar
- **WHEN** 用户已登录但无头像 URL
- **THEN** SidebarFooter 显示昵称首字母作为 AvatarFallback、昵称和用户名

#### Scenario: Display placeholder for unauthenticated user
- **WHEN** 用户未登录
- **THEN** SidebarFooter 显示"未登录"占位信息

