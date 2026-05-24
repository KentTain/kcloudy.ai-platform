## Context

Change #5（migrate-iam-to-shadcn）已将 IAM 模块全面迁移至 shadcn-vue 组件体系。当前状态：
- IAM 模块 11 个页面和 2 个组件已完成 Element Plus → shadcn 迁移
- package.json 中 element-plus 依赖仍然存在
- main.ts 中 Element Plus 全局注册代码仍然存在
- 可能存在其他模块的残留引用

约束条件：
- 前端使用 pnpm 管理，Vue 3 + TypeScript + Vite
- 必须在 #5 完成后执行
- 清理操作需保证不影响其他模块

## Goals / Non-Goals

**Goals:**
- 从 package.json 移除 element-plus 及相关依赖
- 从 main.ts 移除 Element Plus 全局注册代码
- 清理所有 Element Plus 引用残留
- 验证零残留（grep 搜索确认）

**Non-Goals:**
- 不涉及功能性变更
- 不涉及组件迁移或重写
- 不涉及业务逻辑调整

## Decisions

### 决策 1：分阶段清理策略

**选择**：按依赖树自下而上清理：残留代码 → 全局注册 → package.json

**理由**：
- 先清理引用残留可暴露隐藏依赖
- 最后删除 package.json 依赖可触发 TypeScript 编译检查
- 若先删依赖再清代码，IDE 会报大量错误影响排查

**备选方案**：直接删除 package.json 依赖 → 全局搜索修复
- 缺点：编译错误过多，难以定位问题

### 决策 2：全局搜索范围

**选择**：搜索关键词 `el-`、`element-plus`、`ElementPlus`

**理由**：
- `el-` 覆盖所有 Element Plus 组件引用（el-button、el-table 等）
- `element-plus` 覆盖 import 语句和样式引入
- `ElementPlus` 覆盖类型导入和全局对象引用

**搜索命令**：
```bash
grep -r "el-" web/vue/src/
grep -r "element-plus" web/vue/src/
grep -r "ElementPlus" web/vue/src/
```

### 决策 3：残留处理策略

**选择**：逐文件人工审查并移除

**理由**：
- 自动化脚本可能误删（如 `el-` 前缀出现在注释或字符串中）
- 人工审查可确认上下文并避免错误

## Risks / Trade-offs

### 风险 1：其他模块仍依赖 Element Plus

**风险**：IAM 之外的其他模块（如 Demo 演示页面）可能仍使用 Element Plus

**缓解措施**：
- 全局搜索确认所有 `el-` 引用
- 若发现其他模块引用，需先迁移再删除依赖
- 或保留依赖但移除全局注册，改为按需引入

### 风险 2：样式残留

**风险**：Element Plus 样式文件可能影响全局样式

**缓解措施**：
- 搜索 `element-plus/theme-chalk` 等样式引入
- 清理 main.ts 或其他入口文件中的样式 import
- 检查是否有自定义覆盖 Element Plus 样式的代码

### 权衡：彻底清理 vs 保守清理

**选择**：彻底清理

**权衡**：
- 彻底清理减少打包体积和维护负担
- 需要更仔细的测试验证
- 若发现未知依赖可回退部分清理

## Migration Plan

### 阶段 1：搜索残留（只读操作）

```bash
# 搜索组件引用
grep -rn "el-" web/vue/src/

# 搜索依赖引入
grep -rn "element-plus" web/vue/src/

# 搜索类型导入
grep -rn "ElementPlus" web/vue/src/
```

### 阶段 2：清理残留代码

根据阶段 1 结果，逐文件移除：
- import 语句
- 组件使用（模板中的 `<el-*>`）
- 类型引用
- 样式引入

### 阶段 3：移除全局注册

编辑 `web/vue/src/main.ts`：
- 移除 `import ElementPlus from 'element-plus'`
- 移除 `app.use(ElementPlus)`
- 移除 Element Plus 样式引入

### 阶段 4：移除依赖

编辑 `web/vue/package.json`：
- 移除 `element-plus`
- 移除 `@element-plus/icons-vue`（若存在且无其他使用）

### 阶段 5：验证

```bash
# 再次搜索确认零残留
grep -rn "el-" web/vue/src/
grep -rn "element-plus" web/vue/src/

# 编译检查
cd web/vue && pnpm install && pnpm build

# 运行时验证
pnpm dev
```

### 回退策略

若发现未知依赖导致功能异常：
1. 回退 package.json 变更（恢复 element-plus 依赖）
2. 回退 main.ts 变更（恢复全局注册）
3. 分析失败原因并补充迁移工作
