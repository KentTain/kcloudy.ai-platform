## Why

Change #5（migrate-iam-to-shadcn）完成后，项目已全面迁移至 shadcn-vue 组件体系。Element Plus 作为遗留依赖仍然存在于 package.json 和全局注册代码中，增加打包体积和依赖复杂度。彻底清理 Element Plus 依赖可简化依赖树、减少维护负担、避免未来误用。

## What Changes

- **删除 element-plus 依赖**：从 `web/vue/package.json` 移除 `element-plus` 及相关依赖（如 `@element-plus/icons-vue`）
- **删除全局注册代码**：移除 `web/vue/src/main.ts` 中 Element Plus 相关的 import 和 `.use()` 调用
- **清理引用残留**：全局搜索并移除所有 `el-` 前缀组件引用、Element Plus 样式引入、类型导入
- **验证零残留**：通过 grep 搜索确认代码库中无 Element Plus 相关引用

## Capabilities

### New Capabilities

无新增能力规范。此变更为纯清理任务，不引入新功能。

### Modified Capabilities

无规范级变更。此变更不改变任何功能性需求，仅移除未使用的依赖。

## Impact

- 受影响文件：
  - `web/vue/package.json`：删除 element-plus 相关依赖项
  - `web/vue/src/main.ts`：删除 Element Plus 全局注册代码
  - 可能存在的残留文件：需 grep 确认后逐一清理
- 受影响依赖：移除 element-plus、@element-plus/icons-vue 等
- 打包影响：减少打包体积，简化依赖树
- 风险：极低 — 纯清理操作，前提是 #5 已完成且无其他模块使用 Element Plus
