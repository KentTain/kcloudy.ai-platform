## Context

Demo 模块的 HomePage、HealthPage、DatasetsPage 使用旧 CommonXxx 封装组件，视觉风格与 AppPage 骨架和 AdminLayout 新壳不一致。DatasetsPage 缺少 Table 展示能力，数据以简单列表形式呈现。

AppPage 组件已存在（`framework/layouts/components/AppPage.vue`），提供 title/eyebrow/description/actions slots 和 variant 系统。

## Goals / Non-Goals

**Goals:**
- 3 个 Demo 页面迁移到 AppPage 骨架 + shadcn 组件
- HomePage 使用 AppPage + shadcn Card 展示平台功能介绍
- HealthPage 使用 AppPage + shadcn Card/Badge 展示健康状态
- DatasetsPage 使用 AppPage + shadcn Table 展示数据集列表，增加搜索筛选
- 移除 3 个页面中对 CommonCard/CommonButton/CommonLoading 的依赖

**Non-Goals:**
- 不新增数据集 CRUD 操作（创建/编辑/删除仅 UI 展示，不接后端）
- 不改变数据集 store 内部逻辑
- 不修改路由配置
- 不改变 API 调用方式

## Decisions

### D1: AppPage variant 选择

- HomePage: `variant="list"`（功能卡片列表）
- HealthPage: `variant="list"`（状态卡片展示）
- DatasetsPage: `variant="list"`（数据集列表页，带筛选区 + Table）

### D2: DatasetsPage 表格展示

**选择：shadcn Table + 手写列定义**

CommonTable 组件已封装 shadcn Table，但 DatasetsPage 场景简单（3-4 列），直接使用 shadcn Table 子组件（TableHeader/TableBody/TableRow/TableCell）更透明。

替代方案：继续使用 CommonTable — 增加一层封装但无额外收益，与去 CommonXxx 目标矛盾。

### D3: 加载态和空态处理

**选择：shadcn Skeleton 替代 CommonLoading**

AppPage 骨架内使用 Skeleton 做行级加载占位，替代 CommonLoading 的全局 spinner。错误态直接在页面内展示，不依赖 CommonButton 重试按钮。

### D4: Badge 安装

项目当前缺少 shadcn `badge` 组件。需通过 `npx shadcn-vue@latest add badge` 安装，用于 HealthPage 状态标记和 DatasetsPage 数据集标签。

## Risks / Trade-offs

- [Badge 未安装] → 安装前需确认 shadcn-vue CLI 正常工作
- [移除 CommonLoading] → Skeleton 行级占位视觉体验可能不同，需验证效果
- [AppPage height 计算] → AppPage 使用 `h-[calc(100svh-3.5rem)]`，依赖 Navbar 56px 高度，需确认与新壳一致