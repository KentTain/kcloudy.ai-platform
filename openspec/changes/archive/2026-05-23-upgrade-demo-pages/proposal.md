## Why

Demo 模块的 3 个页面（首页、健康检查、数据集列表）仍使用 CommonCard/CommonButton/CommonLoading 等旧封装组件，视觉风格与 AppPage 骨架和 AdminLayout 新壳不一致。数据集页缺少 shadcn Table 展示能力。

## What Changes

- **重写 HomePage.vue**：CommonCard → AppPage + shadcn Card
- **重写 HealthPage.vue**：CommonCard → AppPage + shadcn Card/Badge
- **重写 DatasetsPage.vue**：CommonCard/CommonButton → AppPage + shadcn Table/Input/Button/Badge
- 移除 demo 页对 CommonXxx 组件的依赖

## Capabilities

### New Capabilities

- `demo-pages-ui`: Demo 模块页面的 AppPage 骨架 + shadcn 组件化 UI 规范

### Modified Capabilities

- `demo-module`: 页面组件实现从 CommonXxx 迁移到 shadcn 直接使用

## Impact

- 受影响文件：`web/vue/src/demo/pages/HomePage.vue`、`HealthPage.vue`、`DatasetsPage.vue`
- 受影响依赖：移除对 `CommonCard`、`CommonButton`、`CommonLoading` 的引用
- 依赖 AppPage 组件（已存在于 `framework/layouts/components/AppPage.vue`）
- 路由无变化
- 低风险：这些页面在 AdminLayout 壳内但改动仅限模板层