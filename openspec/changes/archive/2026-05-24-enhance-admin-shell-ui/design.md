## Context

当前项目 Admin Shell UI 基于 shadcn-vue Sidebar 系统构建，已有基础的侧边栏导航、面包屑和页面骨架。对比 kbhub 项目发现，当前 UI 缺少主题切换、增强用户菜单、Header 快捷入口、命令面板和菜单权限过滤等现代化功能。

关键约束：
- 保留现有 `framework/`、`demo/`、`iam/` 模块结构
- 基于 shadcn-vue 组件库，不引入额外 UI 框架
- 所有变更向后兼容

## Goals / Non-Goals

**Goals:**
- 提供亮色/暗色/跟随系统三种主题模式
- 增强用户菜单，包含账号设置和开发者设置入口
- Header 区域增加水平导航和快捷入口
- 实现全局命令面板，支持快速跳转
- 菜单项支持基于权限的动态过滤

**Non-Goals:**
- 不改变现有 Sidebar 组件结构（SidebarProvider/Sidebar/SidebarInset）
- 不改变路由体系（仍使用配置式路由，不迁移到 file-based routing）
- 不实现完整的账号设置页面（仅预留路由入口）
- 不实现完整的开发者设置页面（仅预留路由入口）
- 不改变 AppPage 页面骨架组件

## Decisions

### D1: 主题切换实现方式

**选择**: 基于 `@vueuse/core` 的 `useColorMode` 组合式函数

**理由**:
- `@vueuse/core` 已在项目中间接使用（SidebarProvider 的 `useMediaQuery`、`useEventListener`）
- `useColorMode` 内置 localStorage 持久化和 CSS class 切换
- 与 Tailwind CSS v4 的 dark mode class 策略兼容（`dark:` 变体）

**替代方案**:
- 手动实现 CSS 变量切换 → 需要维护更多代码，且与 shadcn-vue 的 dark mode 不兼容
- Pinia store 管理 → 需要手动处理持久化和 CSS class

### D2: 命令面板触发方式

**选择**: `Cmd/Ctrl + K` 快捷键 + Header 搜索框点击

**理由**:
- `Cmd/Ctrl + K` 是业界标准快捷键（VS Code、Slack、GitHub 等）
- Header 搜索框提供可见的交互入口
- 基于 shadcn-vue Command 组件实现

**替代方案**:
- 仅快捷键触发 → 新用户难以发现功能
- 仅搜索框触发 → 缺少快速触发方式

### D3: Header 水平导航位置

**选择**: 放置在 SidebarTrigger 与面包屑之间，位于 Header 右侧搜索区域之前

**理由**:
- 与 kbhub 项目布局一致
- 核心功能（首页、知识库、健康检查）提供快捷入口
- 仅在 `lg` 屏幕以上显示，避免移动端拥挤

**替代方案**:
- 放在 Sidebar 顶部 → Sidebar 已有菜单，功能冗余
- 放在 Header 最右侧 → 视觉权重不合适

### D4: 菜单权限过滤方式

**选择**: 组合式函数 `useMenuPermission`，基于 Pinia PermissionStore

**理由**:
- 与现有权限系统（`usePermission`、`PermissionStore`）集成
- 无需额外 API 调用，使用已缓存的权限数据
- 默认行为：所有菜单可见，仅在有权限配置时过滤

**替代方案**:
- 纯路由 meta 控制 → 无法处理菜单项级别过滤
- 服务端返回菜单配置 → 增加额外 API 依赖，当前项目暂不支持

### D5: 用户菜单组件拆分

**选择**: 从 `AdminLayout.vue` 中提取 `AppSidebarFooter.vue` 独立组件

**理由**:
- 当前用户菜单代码内嵌在 AdminLayout 中，职责不清晰
- 提取后便于维护和扩展
- 与 kbhub 的 `NavUser.tsx` 对应

**替代方案**:
- 继续内嵌在 AdminLayout → 组件会越来越臃肿
- 放入 `components/` 通用目录 → 用户菜单与框架耦合，不适合通用目录

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| `@vueuse/core` 增加包体积 | 仅引入需要的函数（`useColorMode`），整体包体积影响 < 10KB |
| 命令面板与搜索框交互冲突 | 命令面板使用 Dialog 模态层，搜索框仅触发打开面板 |
| 菜单权限过滤在权限数据未加载时菜单为空 | 默认显示所有菜单，仅在权限数据加载完成后过滤 |
| 水平导航在窄屏下显示拥挤 | 使用 `hidden lg:flex` 仅在大屏显示 |
| 预留路由入口（账号设置/开发者设置）指向空页面 | 创建占位页面，显示"功能开发中"提示 |