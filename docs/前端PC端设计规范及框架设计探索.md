> **文档性质**：探索稿，随讨论迭代。最后更新：2026-05-20（浅色 + 蔚蓝主色 + 橙红辅色）

### 零. 探索上下文（与仓库现状对照）

| 维度 | 设计稿目标 | `web/vue` 现状 | 差距 |
|------|-----------|----------------|------|
| 视觉主题 | 浅色专业后台（蔚蓝 + 橙红点缀） | 浅色 Tailwind 默认（色调未对齐令牌） | 中 |
| 设计令牌 | 语义色 `@theme`（蔚蓝/橙红） | 无 `@theme`，组件内硬编码 `blue-600` 等 | 中 |
| 布局 | 侧栏 + 顶栏 + TagsView + 内容区 | 仅侧栏 + 内容区（`MainLayout.vue`） | 中 |
| UI 组件 | 完整表单/表格/树等规范 | `AppButton/Card/Loading/Modal` 四件套 | 大 |
| 权限 | 动态路由 + `v-permission` | `requiresAuth` 注释占位 | 未开始 |
| 技术栈 | Vue3 + TS + Vite + Pinia + Tailwind | 已对齐；未引入 Element Plus / ECharts | 部分 |

**命名约定（与 `web/README.md` 统一）**：目录使用 `layouts/`、`pages/`（非 `layout/`、`views/`）；业务模块可按 `src/{module}/` 分包（如 `demo/`）。

**已决方向**

- **默认主题**：浅色（已确认）；暗色主题可作为后续扩展，令牌预留 `data-theme` 即可。
- **品牌色**：主色蔚蓝、辅色橙红（见 §一 色板）。

**待决问题（讨论中）**

1. 表格/表单等高频后台组件：**自研 Tailwind** vs **Element Plus 主题覆盖** vs **Headless UI + 自研皮肤**？
2. 橙红辅色使用边界：仅强调/告警类操作，还是允许与蔚蓝并列为双主 CTA？
3. 多技术栈（Vue/React）是否共享**同一套 Design Token**（CSS 变量 / JSON）？

---

### 一. 前端 UI 设计规范 (Admin UI Design System)

**核心美学方向：** 浅色、清爽、高可读的企业后台。以**蔚蓝**建立信任感与导航一致性，以**橙红**点缀关键操作、预警与数据对比；保持硬朗小圆角与高信息密度，避免霓虹/大面积发光等暗色赛博元素。

#### 1. 字体与色彩系统

- **字体系统 (Typography)**
  - **UI 字体**：`Inter`, `SF Pro Display`, `-apple-system`, `BlinkMacSystemFont`, `Roboto`, `PingFang SC`, `Microsoft YaHei`, `sans-serif`。
  - **数据/代码字体**：`JetBrains Mono`, `Roboto Mono`, `monospace`。用于 ID、数值、代码片段。
  - **字重规范**：标题 Bold (700) / SemiBold (600)，正文 Regular (400)，辅助信息 Regular (400) + 次要色。
- **色彩系统 (Color Palette)**

| 语义 | 色值 | 用途 |
|------|------|------|
| 页面背景 `surface` | `#F5F7FA` | 内容区、列表底 |
| 抬升面 `surface-raised` | `#FFFFFF` | 卡片、侧栏、顶栏、弹层 |
| 浅蓝底 `primary-subtle` | `#E8F3FF` | 选中行、信息提示条背景 |
| **主色 蔚蓝** `primary` | `#1677FF` | 主按钮、链接、菜单选中、图表主系列 |
| 主色悬停 `primary-hover` | `#0958D9` | 按钮/链接 hover |
| 主色按下 `primary-active` | `#003EB3` | active |
| **辅色 橙红** `secondary` | `#FF5722` | 次要强调、徽章、图表对比系列、需关注类操作 |
| 辅色悬停 `secondary-hover` | `#E64A19` | 橙红按钮 hover |
| 辅色浅底 `secondary-subtle` | `#FFF3E0` | 警告提示、待办高亮 |
| 成功 `success` | `#10B981` | 成功态（与品牌辅色分离） |
| 警示 `danger` | `#EF4444` | 错误、删除确认（比橙红更「危险」） |
| 一级文字 `text` | `#1F2937` | 标题、正文 |
| 二级文字 `text-muted` | `#6B7280` | 说明、表头辅助 |
| 禁用 `text-disabled` | `#9CA3AF` | 禁用控件 |
| 边框 `border` | `#E5E7EB` | 卡片、输入框默认边框 |
| 边框强调 `border-primary` | `rgba(22, 119, 255, 0.35)` | 聚焦、选中卡片 |

- **配色原则**
  - 界面 80% 为白/浅灰中性色，**蔚蓝**承担导航与主操作，**橙红**克制使用（建议 ≤15% 视觉面积），避免双强色竞争。
  - 橙红用于：待处理数量、重要提醒、对比图表第二序列、「需关注」类按钮；破坏性操作仍优先 `danger` 红而非橙红。
- **令牌落地（Tailwind CSS v4）**：组件只引用语义 class，不写死 Tailwind 默认 `blue-600`。

```css
@theme {
  --color-surface: #f5f7fa;
  --color-surface-raised: #ffffff;
  --color-primary: #1677ff;
  --color-primary-hover: #0958d9;
  --color-primary-subtle: #e8f3ff;
  --color-secondary: #ff5722;
  --color-secondary-hover: #e64a19;
  --color-secondary-subtle: #fff3e0;
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-text: #1f2937;
  --color-text-muted: #6b7280;
  --color-border: #e5e7eb;
  --radius-ui: 6px;
  --font-sans: Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

#### 2. 布局与栅格 (Layout & Grid)

- **栅格系统**：采用 12 列栅格布局，适配 1920px (大屏)、1440px (桌面)、768px (平板) 断点。
- **间距系统**：基于 8px 基准。8px (紧凑)、16px (常规)、24px (卡片内边距)、32px (模块间距)、48px (大区块间距)。
- **视觉层次**：白卡片 (`#FFFFFF`) 置于浅灰页面底 (`#F5F7FA`)，投影 `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08)` + 边框 `#E5E7EB`。
- **圆角规范**：统一 `4px` / `6px`，避免过大圆角削弱专业感。

#### 3. 组件设计规范 (Components)

- **按钮 (Buttons)**
  - **主按钮**：背景蔚蓝 `#1677FF`，文字白色。悬停 `#0958D9`，禁用降透明度。无发光阴影，可用轻微 `shadow-sm`。
  - **强调按钮（辅色）**：背景橙红 `#FF5722`，文字白色。用于「提交审核」「立即处理」等需突出但非主路径的操作；同一操作区最多 1 个。
  - **次按钮**：白底 + 蔚蓝 1px 描边，文字蔚蓝；悬停 `primary-subtle` 底。
  - **幽灵按钮**：透明底，文字 `text-muted`；悬停文字变蔚蓝。
  - **危险按钮**：描边或填充 `danger`，与橙红辅色区分。
- **输入框 (Input Fields)**
  - **常态**：白底 `#FFFFFF`，1px 边框 `#E5E7EB`，圆角 6px。
  - **聚焦态**：边框蔚蓝，外圈 `box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.15)`（替代暗色主题光晕）。
  - **错误态**：边框 `danger`，下方错误文案橙红仅用于非破坏性提示时可改用 `secondary`。
  - **占位符**：`text-disabled`，常规 sans，不用打字机动效。
- **单选/多选框 (Radio & Checkbox)**
  - **未选中**：边框 `#D1D5DB`；**选中**：填充/描边蔚蓝，对勾白色。
  - **交互**：0.2s transition。
- **下拉选择 (Select/Dropdown)**
  - **触发器**：同输入框；Chevron 使用 `text-muted`。
  - **下拉面板**：白底 + 边框 + `shadow-lg`；选项 hover 背景 `#E8F3FF`，选中项文字蔚蓝加粗。
- **手风琴 (Accordion)**
  - **标题栏**：`surface-raised`，底部分割线；展开箭头旋转 90°。
  - **内容区**：浅灰底或白底，左侧可选 3px 蔚蓝竖条表展开态。
- **列表 (List)**
  - **分割线**：`1px solid #E5E7EB`。
  - **悬停**：行背景 `#F5F7FA`，左侧 3px 蔚蓝指示条（与表格行一致）。
- **树与树列表 (Tree & TreeSelect)**
  - **连接线**：`#E5E7EB` 实线；**选中节点**：蔚蓝文字 + `primary-subtle` 背景。
  - **层级缩进**：24px/级。
- **后台高频组件（待细化规格）**：数据表格（排序/筛选/分页/空态）、表单（校验/错误文案）、对话框/抽屉、分页器、日期范围、上传、Tabs、Steps、Tooltip/Popover。表格行悬停可与「列表」规范共用左侧指示条。

#### 1.1 可访问性与动效边界

- 状态须同时具备颜色 + 图标/文案（不单靠颜色区分成功/警告）。
- 动效支持 `prefers-reduced-motion` 降级；页面切换 ≤0.3s，表格微交互 ≤0.2s。
- 蔚蓝主按钮、橙红强调按钮与正文对比度建议 ≥4.5:1（白字 on 主色已满足，浅底橙字需避免）。

----

### 二. 后端管理系统前端框架设计

基于上述 UI 规范，设计一套适用于企业级、高扩展性的后端管理系统框架。

#### 1. 技术栈选型

- **核心框架**：Vue 3 (Composition API) + TypeScript + Vite。
- **UI 组件库（选型倾向）**：以 Tailwind v4 + 自研 `components/ui` 为主；复杂表格/日期等可评估 Element Plus 并按 `@theme` 覆盖，避免双套视觉语言。见下文「分层模型」。
- **状态管理**：Pinia。
- **路由管理**：Vue Router 4。
- **数据可视化**：ECharts 或 AntV G2Plot（浅色主题；主系列蔚蓝 `#1677FF`，对比系列橙红 `#FF5722`）。
- **网络请求**：Axios（封装拦截器）。

#### 2. 分层模型

```
┌─────────────────────────────────────────────────────────────┐
│  Pages / 业务模块 (datasets, demo, system, …)               │
├─────────────────────────────────────────────────────────────┤
│  Features：页面级组合（筛选栏+表格+操作区）                  │
├─────────────────────────────────────────────────────────────┤
│  components/ui：设计系统（Button, Input, Table, Modal…）     │
├─────────────────────────────────────────────────────────────┤
│  layouts：AdminLayout = Sidebar + Navbar + TagsView + Main  │
├─────────────────────────────────────────────────────────────┤
│  横切：router / stores / api / composables / directives     │
└─────────────────────────────────────────────────────────────┘
```

#### 3. 目录结构设计（对齐 `web/vue`）

```text
src/
├── api/                # 按资源或模块划分（client 拦截器集中）
├── assets/
├── components/
│   └── ui/             # 设计系统原子组件
├── composables/        # useModal, usePermission, useTable…
├── layouts/
│   ├── AdminLayout.vue # 壳布局
│   ├── AppSidebar.vue
│   ├── AppNavbar.vue
│   ├── AppTagsView.vue
│   └── AppMain.vue
├── pages/              # 路由页面（或 src/{module}/pages）
├── router/             # 静态路由 + 动态权限路由注册
├── stores/             # user, permission, app(settings/theme)
├── styles/             # @theme 令牌 + 全局 reset
├── types/
├── utils/              # 权限指令、格式化
├── {module}/           # 可选：业务模块内聚 api/components/pages
├── App.vue
└── main.ts
tests/                  # 与 src 镜像，见 web/README
```

#### 4. 核心布局架构

采用经典的  **“侧边栏 + 顶部导航 + 内容区”**  布局，支持响应式折叠。

- **侧边栏 (Sidebar)**：
  - 宽度：展开 240px，折叠 64px。
  - 背景：白色 `#FFFFFF`，右边框 `#E5E7EB`。
  - 菜单项：默认 `text-muted`；选中项文字/图标 `primary`，背景 `primary-subtle`，左侧 3px 蔚蓝指示条。
- **顶部导航 (Navbar)**：
  - 高度：60px；白底，底边框 `#E5E7EB`。
  - 功能：折叠、面包屑、搜索；右侧全屏、消息、用户菜单；主题切换为**可选**（默认可隐藏，仅浅色）。
- **内容区 (AppMain)**：
  - 背景：`#F5F7FA`。
  - **TagsView**：选中标签文字蔚蓝 + 底边 2px `primary`；未选中灰字。紧急/待办角标可用橙红圆点。

#### 5. 权限控制系统

- **路由权限**：后端返回用户拥有的菜单权限列表，前端通过 `router.addRoute()` 动态生成可访问的路由表。未授权路由直接拦截并跳转 403 页面。
- **按钮/操作权限**：封装自定义指令 `v-permission="['user:add', 'user:edit']"`。当用户不具备对应权限码时，自动移除或禁用该 DOM 元素。
- **接口权限**：在 Axios 响应拦截器中统一处理 401 (未登录) 和 403 (无权限) 状态码，自动触发重新登录或权限提示。

**与后端多租户对齐（探针）**：请求头携带租户/用户上下文、菜单与权限码由后端下发，前端 `permission` store 缓存；403/401 与 `docs/后端多租户框架设计方案.md` 保持一致。

#### 6. 交互与动效增强

- **页面切换**：内容区页面切换时，增加 0.3s 的淡入淡出 (Fade) 或 轻微缩放 (Zoom) 效果。
- **数据加载**：表格或图表数据加载时，使用骨架屏 (Skeleton) 代替传统 Loading 转圈，浅灰脉冲动画即可。
- **反馈机制**：顶部 Notification——信息/成功用蔚蓝或绿色系；**需注意**类提示可用橙红描边或图标；错误/危险用 `danger` 红，与橙红辅色区分。

这套规范以浅色为基底、蔚蓝为主、橙红点睛，兼顾企业后台的严谨性、可读性与可维护性。

---

### 三. 实施路线建议（探索结论，非任务承诺）

| 阶段 | 目标 | 产出 |
|------|------|------|
| P0 令牌 | `@theme` + 字体引入 | 浅色 + 蔚蓝/橙红令牌，现有 `App*` 改用语义 class |
| P1 壳布局 | AdminLayout 四件套 | 侧栏折叠、顶栏、TagsView 占位 |
| P2 组件库 | Input/Select/Table/Form | 覆盖 80% CRUD 页面 |
| P3 权限 | 动态路由 + directive | 与后端菜单 API 联调 |
| P4 可视化 | ECharts 浅色主题（蔚蓝/橙红系列色） | 仪表盘类页面 |

**下一步（若进入实现）**：`/opsx:new admin-ui-framework` 或继续在本文档迭代规格细节。
