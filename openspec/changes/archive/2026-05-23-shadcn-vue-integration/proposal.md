## Why

Vue 前端项目当前所有 UI 组件（CommonButton、CommonInput 等）均为手写实现，缺乏统一的组件库支持。项目已确定采用 shadcn-vue + Radix Vue + Tailwind CSS 的 UI 技术方案，但尚未完成集成初始化。需要将 shadcn-vue 引入项目，调整现有组件结构，为 IAM 等业务模块提供开箱即用的组件支持。

## What Changes

- 初始化 shadcn-vue：运行 `npx shadcn-vue@latest init`，创建 `components.json` 配置文件和 `src/lib/utils.ts` 工具文件
- 安装依赖：radix-vue、class-variance-authority、clsx、tailwind-merge、lucide-vue-next（已添加到 package.json）
- 调整组件目录结构：将 `src/components/ui/Common*.vue` 组件移至 `src/components/`，`src/components/ui/` 保留给 shadcn-vue 组件
- 重构现有 Common 组件：使用 shadcn-vue 原语（Radix Vue）替代手写实现，保持 Common 前缀命名
- **BREAKING**: 组件导入路径变更（`ui/CommonButton` → `CommonButton`）

## Capabilities

### New Capabilities

- `shadcn-vue-setup`: shadcn-vue 项目初始化配置，包括 components.json、utils.ts、CSS 变量主题

### Modified Capabilities

- `ui-components`: 组件实现方式从手写改为基于 shadcn-vue/Radix Vue 原语封装
- `design-tokens`: 设计令牌从 Tailwind `@theme` 扩展为 CSS 变量 + Tailwind `@theme` 双轨制，兼容 shadcn-vue 主题系统

## Impact

- **组件目录结构**：`src/components/ui/` 内容调整，导入路径变更
- **依赖**：新增 5 个 npm 包（radix-vue、class-variance-authority、clsx、tailwind-merge、lucide-vue-next）
- **样式系统**：需兼容 shadcn-vue CSS 变量主题与现有 Tailwind @theme 令牌
- **业务模块**：IAM 模块可直接使用 shadcn-vue 组件