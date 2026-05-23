## Why

当前前端 PC 端 Vue 技术栈各业务页面（demo、iam）缺少统一的页面骨架组件，每个页面自行处理标题、描述、操作区的布局和样式，导致：
1. 页面标题/操作区风格不一致（有的用 CommonCard title，有的手写 h1）
2. 页面背景色和间距不统一（有的 padding 1rem，有的 16px）
3. 无法区分不同页面类型（列表页 vs 工作台 vs 详情页）的视觉风格

借鉴 kbhub 项目 `KbhubPage.vue` 的页面骨架设计，创建 `AppPage` 组件统一所有页面的头部区域，为后续 #2-#5 变更提供基础设施。

## What Changes

- 新增 `AppPage.vue` 页面骨架组件，提供 title/eyebrow/description/actions/variant 的标准页面头部
- 支持 4 种页面变体（list/workbench/detail/governance），控制背景色与布局风格
- 提供 `actions` slot 用于页面级操作按钮区，`default` slot 用于页面主体内容
- 纯加法变更，不改动任何现有文件，后续页面升级时逐步引入 AppPage

## Capabilities

### New Capabilities

- `page-skeleton`: 页面骨架组件 AppPage，统一 title/eyebrow/description/actions 区域布局，支持 list/workbench/detail/governance 四种页面变体

### Modified Capabilities

（无 — 本变更不修改任何现有 spec 的需求，只新增一个独立能力）

## Impact

- 新增文件：`web/vue/src/framework/layouts/components/AppPage.vue`（1 个文件）
- 不影响现有页面：AppPage 是可选组件，现有页面无需改动即可继续工作
- 不影响 API、store、路由：纯 UI 层变更
- 不引入新依赖：使用已有的 shadcn-vue + Tailwind CSS
- 后续变更依赖：#2 modernize-admin-shell、#3 upgrade-auth-pages、#4 upgrade-demo-pages、#5 migrate-iam-to-shadcn 均会使用 AppPage