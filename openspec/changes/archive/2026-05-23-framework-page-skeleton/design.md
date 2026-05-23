## Context

当前 `web/vue/src/framework/layouts/` 提供了 AdminLayout、AppSidebar、AppNavbar、AppTagsView、AppMain 五个布局组件，但缺少页面级骨架组件。各业务页面（demo、iam）自行处理标题、描述、操作区布局，导致风格不一致。

借鉴 kbhub 项目 `KbhubPage.vue`（38 行）的设计模式，创建 `AppPage.vue` 作为统一页面头部区域的标准组件。

**当前状态**：
- HomePage 用 CommonCard 包裹标题
- HealthPage 用 CommonCard 包裹标题
- DatasetsPage 用 CommonCard header + 手写布局
- IAM 页面用 el-card shadow="never" 包裹
- 各页面 padding、背景色、标题风格不统一

**约束**：
- 只新增组件，不改动任何现有文件
- 使用已有的 shadcn-vue + Tailwind CSS，不引入新依赖
- 保留现有的 framework/ 目录结构

## Goals / Non-Goals

**Goals:**
- 创建 AppPage.vue 页面骨架组件，统一所有页面的 title/eyebrow/description/actions 区域
- 支持 4 种页面变体控制视觉风格
- 为后续 #2-#5 变更提供可复用的页面基础

**Non-Goals:**
- 不升级 AdminLayout/AppSidebar/AppNavbar（属于 #2 变更）
- 不替换任何现有页面的实现（属于 #3/#4/#5 变更）
- 不修改现有 store/api/router
- 不引入 file-based routes 或 kbhub 的 feature/service 模式

## Decisions

### 决策 1: 组件命名 — AppPage vs KbhubPage

**选择**: `AppPage`

**原因**: 项目命名体系是 AppXxx（AppSidebar、AppNavbar、AppMain、AppForm、AppFormItem），保持一致性。KbhubPage 是 kbhub 项目的业务命名，不应照搬。

**备选**: KbhubPage、FrameworkPage、PageShell

### 决策 2: 组件放置位置

**选择**: `framework/layouts/components/AppPage.vue`

**原因**: AppPage 是布局级组件，与 AppMain、AppNavbar 同层。它属于"壳内的页面级骨架"，而非独立 UI 组件（不放在 components/），也非业务模块组件。

**备选**: `framework/components/AppPage.vue`、`components/AppPage.vue`

### 决策 3: 页面变体设计

**选择**: 4 种变体 — `list`、`workbench`、`detail`、`governance`

| variant | 背景 | 适用场景 |
|---------|------|----------|
| list | `bg-background`（#F5F7FA） | 列表页（知识库列表、用户列表等） |
| workbench | `bg-muted/20` | 工作台（问答、编辑器等沉浸式页面） |
| detail | `bg-background` | 详情页（知识库配置、用户详情） |
| governance | `bg-background` | 管理页（标签管理、权限管理） |

**原因**: 借鉴 kbhub KbhubPage 的 variant 设计，list 和 detail 用标准背景，workbench 用略深的 muted 背景，适合沉浸式操作。默认 variant 为 `list`，覆盖大多数场景。

**备选**: 只做 list/workbench 两种，不做 detail/governance 区分（过度简化，不够灵活）

### 冰策 4: 容器高度计算

**选择**: `h-[calc(100svh-3.5rem)]`（借鉴 kbhub KbhubPage）

**原因**: 使用 `svh`（small viewport height）而非 `vh`，避免移动端地址栏影响。3.5rem（56px）对应 header 高度，确保页面内容区恰好填满可视区域。

**注意**: 当前 AppNavbar 高度是 60px + AppTagsView 32px = 92px，后续 #2 变更会调整 header 为 56px（3.5rem）。本变更先按 56px 设计，当前阶段 AppPage 内部的 min-h-full 保证内容不会被截断。

## Risks / Trade-offs

- [AppPage 高度计算与当前 header 不匹配] → 使用 min-h-full 作为 fallback，内容区不会被截断，后续 #2 调整 header 高度后精确匹配
- [4 种 variant 可能过度设计] → variant 只是背景色差异，实现成本极低（1 行 computed），不增加维护负担
- [eyebrow 字段可能多数页面不使用] → eyebrow 是可选 prop，不传就不渲染，零成本