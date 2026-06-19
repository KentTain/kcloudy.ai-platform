## Context

Vue 前端项目有 7 个手写 Common 组件（CommonButton、CommonCard、CommonInput、CommonModal、CommonSelect、CommonTable、CommonLoading），位于 `src/components/ui/`。这些组件基于 Tailwind CSS + CSS 自定义属性实现样式，功能完整但缺乏可访问性支持（键盘导航、ARIA 属性）。

项目已确定采用 shadcn-vue + Radix Vue + Tailwind CSS 作为 UI 技术方案。package.json 已添加相关依赖，但尚未完成项目初始化和组件迁移。

当前设计令牌通过 Tailwind v4 `@theme` 指令定义（tokens.css），shadcn-vue 使用 CSS 变量约定（`--primary`、`--background` 等），两者需要兼容。

## Goals / Non-Goals

**Goals:**

- 完成 shadcn-vue 项目初始化（components.json、utils.ts、CSS 变量主题）
- 调整组件目录结构，`ui/` 目录保留给 shadcn-vue 原生组件
- 重构 Common 组件为基于 Radix Vue/shadcn-vue 原语的封装
- 统一设计令牌系统，兼容 shadcn-vue CSS 变量与现有 Tailwind @theme

**Non-Goals:**

- 不引入暗色主题实现（仅预留接口）
- 不重构 React 前端（尚未创建）
- 不修改后端 API
- 不添加 shadcn-vue 尚未需要的额外组件

## Decisions

### Decision 1: 目录结构调整

**选择**: `src/components/ui/` → shadcn-vue 组件，Common 组件 → `src/components/`

**理由**: shadcn-vue CLI 默认将组件输出到 `components/ui/`，与项目文档约定一致。Common 组件是业务封装层，不属于 UI 原语层。

**替代方案**: 保持 Common 组件在 `ui/` 下 — 违反分层约定，且 shadcn-vue CLI 会覆盖同名目录。

### Decision 2: Common 组件重构策略

**选择**: 逐步替换，保持 Common 前缀命名

**理由**: Common 组件提供了业务级封装（loading 状态、prefix/suffix、size 变体），这些超出 shadcn-vue 原语的范围。保留 Common 前缀可以明确区分"UI 原语"和"业务封装"两层。

**替代方案**: 直接使用 shadcn-vue 组件替代 Common 组件 — 会丢失业务封装功能（如 CommonButton 的 loading 状态），导致业务代码变复杂。

**映射关系**:

| Common 组件 | shadcn-vue 原语 | 重构方式 |
|---|---|---|
| CommonButton | Button | 基于 shadcn Button 扩展 loading/block |
| CommonCard | Card | 基于 shadcn Card 封装 shadow/padding |
| CommonInput | Input + FormControl | 基于 shadcn Input 扩展 clearable/error |
| CommonModal | Dialog | 基于 shadcn Dialog 封装 size/maskClosable |
| CommonSelect | Select | 基于 shadcn Select 封装 options/clearable |
| CommonTable | Table | 基于 shadcn Table 封装 columns/loading |
| CommonLoading | 自定义 Spinner | 无 shadcn 对应，保留手写实现 |

### Decision 3: 设计令牌双轨制

**选择**: shadcn-vue CSS 变量 + Tailwind @theme 令牌共存

**理由**: shadcn-vue 组件内部引用 CSS 变量（`--primary`、`--background`），而现有组件和 Tailwind 类引用 @theme 令牌（`bg-primary`、`text-text-muted`）。两套系统需要映射对齐。

**实现**: 在 tokens.css 中同时定义 CSS 变量和 @theme 令牌，确保语义一致：

```css
@theme {
  --color-primary: var(--primary);        /* shadcn CSS var → Tailwind */
  --color-primary-foreground: var(--primary-foreground);
  --color-background: var(--background);
  --color-surface: var(--surface);
}
```

**替代方案**: 完全迁移到 shadcn CSS 变量 — 会破坏现有组件的 Tailwind 类名引用。

## Risks / Trade-offs

- **[导入路径变更]** → 所有引用 `ui/CommonButton` 的业务模块需更新导入路径，影响面包括 demo、framework、iam 模块
- **[shadcn-vue CSS 变量与现有 @theme 冲突]** → 双轨制增加维护复杂度，需确保语义色值一致
- **[Common 组件重构期间功能回归]** → 逐步替换，每个组件独立重构和测试，避免批量变更
- **[shadcn-vue CLI 版本变更]** → 锁定 components.json 配置，避免 CLI 升级导致组件格式变化