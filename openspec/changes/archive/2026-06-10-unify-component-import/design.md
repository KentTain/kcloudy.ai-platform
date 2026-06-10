## 上下文

### 当前状态

Vue 前端存在两套组件导入入口：

```
@/components/ui/      ← shadcn 原始组件（30+ 组件组）
@/components/common/  ← 业务封装组件（18 个组件）
```

**问题现象**：
- tenant 模块 12 个文件中，85% 的组件从 `ui/` 导入，仅 15% 从 `common/` 导入
- iam、demo 等模块情况类似
- common 提供的业务增强（loading、clearable、error）未被利用

**根本原因**：
1. 同名组件存在两份，开发者默认选择"更底层"的 ui/
2. 缺少统一入口，没有明确的优先级指引
3. common 的价值未被充分传达

### 约束

- 不能破坏现有导入路径（向后兼容）
- 不能影响 tree-shaking
- 不能新增外部依赖
- ui/Tree 与 common/Tree 数据结构不兼容，需特殊处理

## 目标 / 非目标

**目标：**
- 建立 `@/components` 统一入口，common 优先 + 高频 ui 兜底
- 迁移 42 个业务模块文件到新入口
- 通过文档 + memory 强化 Claude 的组件选择约束

**非目标：**
- 不修改 common/ 和 ui/ 目录下的组件实现
- 不删除现有导入路径（ui/xxx、common 均保留）
- 不引入 ESLint 规则强制约束（仅文档 + memory）
- 不处理 ai-elements/ 组件（AI 专用，独立入口）

## 决策

### 决策 1：统一入口导出策略

**选择**：common 优先 + 高频 ui 重导出

**理由**：
- common 组件是 ui 的业务超集，完全兼容并可替代
- 高频 ui 组件（Badge, Dialog, Tabs, Form 等）进统一入口，覆盖 90% 使用场景
- 低频 ui 组件（Sidebar, Accordion, HoverCard 等）保持从 `ui/xxx` 导入

**替代方案**：
- ❌ 仅导出 common：需要记住哪些在 common，哪些在 ui
- ❌ 全量重导出：入口文件庞大，tree-shaking 可能受影响
- ✅ common + 高频 ui：平衡覆盖率和入口大小

### 决策 2：同名组件处理

**选择**：统一入口中 common 覆盖 ui

**组件映射**：

| 组件 | 统一入口来源 | 覆盖理由 |
|------|-------------|---------|
| Button | common | +loading/block/type，业务变体映射 |
| Input | common | +clearable/error/prefix/suffix slots |
| Card | common | +title/shadow/padding/header/footer slots |
| Select | common | 声明式 options，替代 ui 手动组装 |
| Table | common | 声明式 columns+data，替代 ui 手动组装 |
| Tree | **不导出** | common/Tree 与 ui/Tree 不兼容，需显式指定路径 |

**替代方案**：
- ❌ 两个都导出用别名：`Button` vs `UiButton`，增加记忆负担
- ❌ 保留 ui 版本：业务封装价值浪费
- ✅ common 覆盖：迁移后代码更简洁，自动获得业务增强

### 决策 3：ui/Tree 特殊处理

**选择**：不进入统一入口，保持 `@/components/ui/tree` 路径

**理由**：
- common/Tree 使用 `TreeComponentNode`（id/name/children）
- ui/Tree 使用 `TreeNodeType`（value/label/children）
- 两者数据结构不兼容，功能定位不同
- 强制开发者显式选择，避免混淆

### 决策 4：约束方式

**选择**：文档强化 + memory 约束（不用 ESLint）

**理由**：
- 目标是约束 Claude 行为，不是团队开发规范
- CLAUDE.md + memory 足以影响 Claude 的组件选择
- ESLint 规则维护成本高，需要 AST 分析 common 覆盖清单

## 风险 / 权衡

### 风险 1：迁移后组件行为变化

**风险**：从 ui/Button 切换到 common/Button，props 可能不兼容

**缓解**：
- 已完成 API 兼容性分析，common 是 ui 的超集
- common/Button 的 variant 映射：primary→default, danger→destructive
- 迁移时逐文件验证，确保无运行时错误

### 风险 2：开发者习惯改变

**风险**：团队开发者可能继续从 ui/ 导入

**缓解**：
- 文档明确说明统一入口的优势
- 后续 Code Review 提醒使用统一入口
- 可考虑后续添加 ESLint 规则（本期不做）

### 风险 3：tree-shaking 效果

**风险**：统一入口可能影响 tree-shaking

**缓解**：
- 使用命名导出而非默认导出
- Vite 对 ES 模块 tree-shaking 支持良好
- 测试构建产物大小变化

## 迁移计划

### 阶段 1：创建统一入口

1. 创建 `web/vue/src/components/index.ts`
2. 实现 common 优先 + 高频 ui 重导出逻辑
3. 导出所有类型定义

### 阶段 2：迁移业务模块

按模块顺序迁移（每个模块完成后验证）：

1. **tenant** (12 文件) - 问题发现源头，优先处理
2. **iam** (11 文件) - 业务逻辑复杂，需仔细验证
3. **demo** (4 文件) - 简单，快速完成
4. **framework** (12 文件) - 基础设施，最后处理
5. **ai** (3 文件) - 模块最小

### 阶段 3：文档 + memory 强化

1. 更新 `web/vue/src/CLAUDE.md`
2. 更新 `web/vue/src/components/common/CLAUDE.md`
3. 写入 memory 文件 `component-import-priority.md`

### 阶段 4：验证

1. 运行 `pnpm dev` 验证开发模式
2. 运行 `pnpm build` 验证生产构建
3. 运行 `pnpm test:unit` 验证测试通过

## 开放问题

无 —— 所有设计决策已确定。
