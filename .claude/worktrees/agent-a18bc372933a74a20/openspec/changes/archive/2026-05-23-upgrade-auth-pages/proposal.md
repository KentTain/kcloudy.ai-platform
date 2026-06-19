## Why

当前登录页、403 和 404 页面仍使用 CommonCard/CommonInput/CommonButton 等旧封装组件，视觉风格与已完成的 AdminLayout 新壳（shadcn SidebarProvider）不一致。登录页缺少表单校验（vee-validate + zod）和两列品牌布局，错误页风格各自独立未统一。

## What Changes

- **重写 LoginPage.vue**：CommonCard/CommonInput → shadcn Card/FormField/Input + vee-validate + zod 校验，借鉴 kbhub login.vue 两列布局（品牌区 + 表单区）
- **重写 ForbiddenPage.vue**：CommonButton → shadcn Button，统一错误页视觉风格
- **重写 NotFoundPage.vue**：CommonButton → shadcn Button，统一错误页视觉风格
- 移除上述 3 个页面中对 CommonXxx 组件的依赖

## Capabilities

### New Capabilities

- `auth-pages-ui`: 登录页、403、404 页面的 shadcn 组件化 UI 规范

### Modified Capabilities

- `authentication`: 登录表单校验从手写 ref 验证升级为 vee-validate + zod schema

## Impact

- 受影响文件：`web/vue/src/framework/pages/LoginPage.vue`、`ForbiddenPage.vue`、`NotFoundPage.vue`
- 受影响依赖：移除对 `CommonCard`、`CommonInput`、`CommonButton` 的引用，新增 `vee-validate`、`@vee-validate/zod`、`zod` 依赖
- 路由无变化：`/login`、`/403`、404 catch-all 保持不变
- 低风险：这些页面不在 AdminLayout 壳内，独立渲染，改动不影响壳内页面