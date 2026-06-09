# common-smart-tooltip 规格

## 概述

智能溢出检测提示组件，仅在文本溢出时显示 tooltip。

## 功能需求

### 核心功能

- 文本溢出检测（单行/多行）
- 仅在溢出时显示 tooltip
- 支持自定义内容
- 支持自定义样式类

### 组件 API

**Props:**

```typescript
interface SmartTooltipProps {
  content: string                    // 提示内容
  contentClass?: HTMLAttributes['class']  // 内容样式类
  onlyEllipsisOpen?: boolean         // 仅在溢出时显示
  class?: HTMLAttributes['class']    // 触发器样式类
}
```

**Slots:**

- 默认插槽：触发器内容
- tooltip-content：自定义 tooltip 内容

## 迁移来源

- 源文件：`D:\Project\ai\Alon\apps\kbhub\web\src\components\alon\alon-tooltip\`
- 目标位置：`web/vue/src/components/common/feedback/tooltip/`

## 文件清单

| 源文件 | 目标文件 |
|--------|----------|
| AlonTooltip.vue | SmartTooltip.vue |
| index.ts | index.ts |

## 依赖

- @chenglou/pretext@0.0.7（新增）
- ui/tooltip

## 验收标准

- [ ] 组件迁移完成，文件位置正确
- [ ] 重命名完成（AlonTooltip -> SmartTooltip）
- [ ] 溢出检测逻辑正常工作
- [ ] 构建通过
