# Components 通用组件目录

## 概述

`components/` 目录存放技术栈级通用组件。前端 PC 端采用两层组件组织结构：

| 层级 | 目录 | 说明 |
|------|------|------|
| 技术栈通用组件 | `web/{技术栈}/src/components/` | 跨模块共享，业务无关 |
| 模块级通用组件 | `web/{技术栈}/src/{模块}/components/` | 模块专用，与模块功能耦合 |

**与 `framework/components/` 的区别：**

| 目录 | 定位 | 使用场景 |
|------|------|----------|
| `src/components/` | 技术栈通用组件 | 纯 UI 展示、无业务依赖、可复用到任意模块 |
| `framework/components/` | 框架级组件 | 与布局、权限、表单等框架功能耦合 |

## 目录结构

```text
components/
├── ui/                        # UI 基础组件（通用组件）
│   ├── CommonButton.vue       # 按钮
│   ├── CommonCard.vue         # 卡片
│   ├── CommonInput.vue        # 输入框
│   ├── CommonLoading.vue      # 加载
│   ├── CommonModal.vue        # 弹窗
│   ├── CommonSelect.vue       # 下拉选择
│   └── CommonTable.vue        # 数据表格
├── common/                    # 通用业务组件（预留）
│   ├── EmptyState.vue         # 空状态
│   └── ErrorBoundary.vue      # 错误边界
└── CLAUDE.md                  # 本文档
```

## 组件分类

| 目录 | 说明 | 示例 |
|------|------|------|
| `ui/` | 基础 UI 组件 | Button、Input、Modal |
| `common/` | 通用业务组件 | EmptyState、ErrorBoundary |

## 组件命名规范

前端 PC 端采用统一的前缀命名规范，区分不同层级的组件：

| 层级 | 目录 | 前缀 | 示例 | 说明 |
|------|------|------|------|------|
| 技术栈通用组件 | `src/components/` | `Common` | `CommonButton` | 跨模块共享的基础组件 |
| 模块级通用组件 | `{模块}/components/` | `{模块}` | `DemoDatasetCard` | 模块专用组件，带模块前缀 |
| 框架级组件 | `framework/components/` | `App` | `AppForm` | 与框架功能耦合的组件 |

### 命名示例

```text
# 技术栈通用组件 (src/components/ui/)
CommonButton.vue       # 按钮
CommonInput.vue        # 输入框
CommonModal.vue        # 弹窗

# 模块级组件 (demo/components/)
DemoDatasetCard.vue    # Demo 模块 - 数据集卡片
DemoDatasetForm.vue    # Demo 模块 - 数据集表单

# 框架级组件 (framework/components/)
AppForm.vue            # 表单框架
AppFormItem.vue        # 表单项
AdminLayout.vue        # 管理后台布局
```

### 命名规则

1. **技术栈通用组件**：使用 `Common` 前缀，表示全局可复用
2. **模块级组件**：使用模块名作为前缀（如 `Demo`、`Iam`），便于识别来源
3. **框架级组件**：使用 `App` 前缀，表示框架提供的基础设施
4. **布局组件**：使用 `Admin`、`Layout` 等前缀，表示布局用途

### 组件结构

```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup lang="ts">
// 类型定义
interface Props {
  variant?: "primary" | "secondary";
}

// Props 定义
const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
});

// Emits 定义
const emit = defineEmits<{
  click: [event: MouseEvent];
}>();
</script>
```

### 最佳实践

1. **Props 设计**
   - 提供合理的默认值
   - 使用 TypeScript 类型约束
   - 避免可选 props 过多

2. **事件命名**
   - 使用 kebab-case
   - 避免与原生事件重名

3. **样式隔离**
   - 使用 scoped CSS
   - 优先使用 Tailwind 类

4. **可访问性**
   - 添加必要的 ARIA 属性
   - 支持键盘导航

## 使用示例

```typescript
// 在业务模块中引入
import CommonButton from "@/components/ui/CommonButton.vue";
import EmptyState from "@/components/common/EmptyState.vue";
```

## 与 Framework 组件的关系

| 组件来源 | 使用场景 |
|----------|----------|
| `src/components/` | 纯 UI 展示、无框架依赖 |
| `framework/components/` | 需要访问路由、状态、权限 |

## 组件迁移分析

现有 `framework/components/ui/` 中的组件，已迁移至 `src/components/ui/`：

| 组件 | 迁移状态 | 新名称 |
|------|----------|--------|
| AppButton | ✅ 已迁移 | CommonButton |
| AppCard | ✅ 已迁移 | CommonCard |
| AppInput | ✅ 已迁移 | CommonInput |
| AppLoading | ✅ 已迁移 | CommonLoading |
| AppModal | ✅ 已迁移 | CommonModal |
| AppSelect | ✅ 已迁移 | CommonSelect |
| AppTable | ✅ 已迁移 | CommonTable |
| AppForm | ⏸️ 保留 | AppForm（框架级组件） |
| AppFormItem | ⏸️ 保留 | AppFormItem（框架级组件） |

### 使用方式

迁移后的技术栈通用组件直接从 `src/components/ui/` 引入：

```typescript
import CommonButton from "@/components/ui/CommonButton.vue";
```

## 注意事项

1. 新增通用组件前，确认是否已存在于 `src/components/ui/`
2. 避免在通用组件中引入业务逻辑或框架依赖
3. 保持组件 API 稳定，变更需考虑影响范围
