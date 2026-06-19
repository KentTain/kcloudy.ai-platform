## 1. 基础设施准备

- [x] 1.1 安装 `@vueuse/core` 依赖（pnpm add @vueuse/core）
- [x] 1.2 通过 shadcn-vue CLI 添加 Command 组件（npx shadcn-vue@latest add command）
- [x] 1.3 通过 shadcn-vue CLI 添加 NavigationMenu 组件（npx shadcn-vue@latest add navigation-menu）
- [x] 1.4 确认 Tailwind CSS v4 dark mode 配置正确（dark: 变体生效）

## 2. 主题切换（P0）

- [x] 2.1 创建 `framework/composables/useColorMode.ts`，基于 @vueuse/core 的 useColorMode 封装
- [x] 2.2 创建 `framework/layouts/components/AppSidebarFooter.vue`，提取 AdminLayout 中用户菜单为独立组件
- [x] 2.3 在 AppSidebarFooter 中添加用户下拉菜单（用户信息 + 主题切换 + 账号设置 + 开发者设置 + 退出登录）
- [x] 2.4 替换 AdminLayout.vue 中 SidebarFooter 内联代码为 AppSidebarFooter 组件
- [x] 2.5 编写 AppSidebarFooter 组件单元测试

## 3. 用户菜单增强（P1）

- [x] 3.1 创建 `framework/pages/AccountSettingsPage.vue` 占位页面（"功能开发中"提示）
- [x] 3.2 创建 `framework/pages/DeveloperSettingsPage.vue` 占位页面
- [x] 3.3 在 framework/router/index.ts 中添加 `/settings/account` 和 `/settings/developer` 路由
- [x] 3.4 完善 AppSidebarFooter 用户信息展示（头像/AvatarFallback + 昵称 + 用户名）

## 4. Header 快捷入口（P2）

- [x] 4.1 重构 `AppNavbar.vue`，增加右侧区域布局（搜索 + 快捷按钮）
- [x] 4.2 在 AppNavbar 中集成 NavigationMenu 水平导航（首页、知识库等核心入口，lg 屏以上显示）
- [x] 4.3 在 AppNavbar 中添加搜索触发区域（点击打开命令面板）
- [x] 4.4 在 AppNavbar 中添加快捷操作按钮（待办、通知图标按钮，预留路由入口）
- [x] 4.5 编写 AppNavbar 组件单元测试

## 5. 命令面板（P3）

- [x] 5.1 创建 `framework/components/CommandPalette.vue` 全局命令面板组件
- [x] 5.2 实现命令面板搜索逻辑（基于菜单项列表 + 关键词匹配）
- [x] 5.3 实现命令面板快捷键 `Cmd/Ctrl + K` 触发（全局事件监听）
- [x] 5.4 实现命令面板路由跳转和关闭行为
- [x] 5.5 在 AppNavbar 搜索区域集成 CommandPalette 触发
- [x] 5.6 编写 CommandPalette 组件单元测试

## 6. 菜单权限过滤（P4）

- [x] 6.1 创建 `framework/composables/useMenuPermission.ts`，基于 PermissionStore 实现菜单过滤
- [x] 6.2 修改 `AppNavMain.vue`，接收 filteredItems props 并支持权限过滤
- [x] 6.3 为 AppNavMain 菜单项添加 permissionKey 属性（如 `iam.users`、`iam.roles`）
- [x] 6.4 实现分组级别过滤（当分组内所有菜单项被过滤后隐藏整组）
- [x] 6.5 编写 useMenuPermission 组合式函数单元测试

## 7. 验收与清理

- [x] 7.1 全局类型检查（pnpm type-check）
- [x] 7.2 代码质量检查（pnpm check）
- [x] 7.3 运行所有单元测试（pnpm test:unit -- --run）
- [ ] 7.4 启动开发服务器，手动验证所有功能