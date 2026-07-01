# 统一消息提醒组件设计规格

## 概述

统一前端项目的消息提醒组件，使用 vue-sonner + shadcn-vue 封装，提供一致的 Toast 通知体验。

## 设计决策

| 配置项 | 决策 | 理由 |
|--------|------|------|
| 技术方案 | shadcn-vue Sonner 封装 | 与项目现有 shadcn-vue 生态一致，Alon 项目已验证可行 |
| 显示位置 | top-center（顶部居中） | 不遮挡侧边栏导航和右侧操作区域，视觉焦点集中 |
| 样式风格 | rich-colors: true | 视觉区分度高，用户一眼识别消息类型 |
| 自动关闭 | 4 秒（默认值） | vue-sonner 默认值，足够用户阅读简短消息 |
| 多消息处理 | 合并相同消息 + 限制最大数量 | 最佳用户体验，避免消息刷屏 |

## 技术实现

### 1. 添加依赖

```bash
pnpm add vue-sonner
```

### 2. 创建 Sonner 组件封装

**路径**：`web/vue/src/components/ui/sonner/Sonner.vue`

```vue
<script lang="ts" setup>
import { CircleCheckIcon, InfoIcon, Loader2Icon, OctagonXIcon, TriangleAlertIcon, XIcon } from "lucide-vue-next"
import { Toaster, type ToasterProps } from "vue-sonner"
import { cn } from "@/lib/utils"

const props = defineProps<ToasterProps>()
</script>

<template>
  <Toaster
    :class="cn('toaster group', props.class)"
    :style="{
      '--normal-bg': 'var(--popover)',
      '--normal-text': 'var(--popover-foreground)',
      '--normal-border': 'var(--border)',
      '--border-radius': 'var(--radius)',
    }"
    v-bind="props">
    <template #success-icon> <CircleCheckIcon class="size-4" /> </template>
    <template #info-icon> <InfoIcon class="size-4" /> </template>
    <template #warning-icon> <TriangleAlertIcon class="size-4" /> </template>
    <template #error-icon> <OctagonXIcon class="size-4" /> </template>
    <template #loading-icon>
      <div><Loader2Icon class="size-4 animate-spin" /></div>
    </template>
    <template #close-icon> <XIcon class="size-4" /> </template>
  </Toaster>
</template>
```

**路径**：`web/vue/src/components/ui/sonner/index.ts`

```typescript
export { default as Toaster } from "./Sonner.vue";
```

### 3. 全局注册 Toaster

**路径**：`web/vue/src/App.vue`

```vue
<script setup lang="ts">
import { Toaster } from "@/components/ui/sonner"
</script>

<template>
  <RouterView />
  <Toaster position="top-center" rich-colors :visibleToasts="3" />
</template>
```

### 4. 更新 feedback.ts

**路径**：`web/vue/src/framework/utils/feedback.ts`

```typescript
import { toast } from "vue-sonner"

export const notifySuccess = (message: string, options?: { id?: string; duration?: number }) => {
  toast.success(message, options)
}

export const notifyError = (message: string, options?: { id?: string; duration?: number }) => {
  toast.error(message, options)
}

export const notifyWarning = (message: string, options?: { id?: string; duration?: number }) => {
  toast.warning(message, options)
}

export const notifyInfo = (message: string, options?: { id?: string; duration?: number }) => {
  toast.info(message, options)
}

// 批量操作专用 API
export const notifyBatchSuccess = (count: number, action: string) => {
  toast.success(`${action}成功`, {
    id: `batch-${action}`,
    description: `已处理 ${count} 项`
  })
}

export const notifyBatchError = (count: number, action: string) => {
  toast.error(`${action}失败`, {
    id: `batch-${action}`,
    description: `${count} 项处理失败`
  })
}

// 保留原有的 confirmAction 和 getErrorMessage
export const confirmAction = (message: string) => window.confirm(message)

export const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { msg?: string; detail?: string } } }).response
    return response?.data?.msg || response?.data?.detail || fallback
  }

  if (error instanceof Error) {
    return error.message || fallback
  }

  return fallback
}
```

## 使用方式

### 基础用法

```typescript
import { notifySuccess, notifyError, notifyWarning, notifyInfo } from '@/framework/utils/feedback'

// 成功提示
notifySuccess('租户创建成功')

// 错误提示
notifyError('网络连接失败')

// 警告提示
notifyWarning('该操作不可撤销')

// 信息提示
notifyInfo('正在处理中...')
```

### 批量操作

```typescript
import { notifyBatchSuccess, notifyBatchError } from '@/framework/utils/feedback'

// 批量删除成功
notifyBatchSuccess(10, '删除')
// 显示：删除成功 - 已处理 10 项

// 批量导入失败
notifyBatchError(5, '导入')
// 显示：导入失败 - 5 项处理失败
```

### 合并相同消息

```typescript
import { notifySuccess } from '@/framework/utils/feedback'

// 使用相同 ID，多次调用只显示一次
notifySuccess('保存成功', { id: 'save' })
notifySuccess('保存成功', { id: 'save' })  // 不会重复显示
```

### 自定义持续时间

```typescript
import { notifyError } from '@/framework/utils/feedback'

// 错误消息显示更长时间
notifyError('操作失败', { duration: 5000 })
```

### 高级用法

```typescript
import { toast } from 'vue-sonner'

// 带操作按钮
toast('文件已删除', {
  action: {
    label: '撤销',
    onClick: () => console.log('撤销')
  }
})

// 加载状态
const toastId = toast.loading('正在保存...')
// 完成后更新
toast.success('保存成功', { id: toastId })
```

## 实现步骤

1. **添加依赖**：执行 `pnpm add vue-sonner`
2. **创建组件**：创建 `web/vue/src/components/ui/sonner/` 目录和相关文件
3. **全局注册**：在 `App.vue` 中注册 `<Toaster>` 组件
4. **更新工具函数**：修改 `framework/utils/feedback.ts` 使用 toast API
5. **验证兼容性**：确保所有现有代码无需修改（API 兼容）
6. **编写测试**：验证功能正常

## 影响范围

### 受影响模块

- `framework/utils/feedback.ts` - 核心修改
- `framework/stores/*` - 使用 feedback 工具
- `tenant/stores/*` - 使用 feedback 工具
- `tenant/pages/*` - 使用 feedback 工具
- `iam/stores/*` - 使用 feedback 工具
- `iam/pages/*` - 使用 feedback 工具

### 向后兼容

所有现有代码无需修改，因为：
- `notifySuccess`、`notifyError`、`notifyWarning` 等函数签名保持不变
- `confirmAction` 和 `getErrorMessage` 保持不变
- 新增的批量操作 API 为可选功能

## 测试计划

### 单元测试

- 测试 `notifySuccess`、`notifyError`、`notifyWarning`、`notifyInfo` 正确调用 toast API
- 测试 `notifyBatchSuccess`、`notifyBatchError` 生成正确的消息格式
- 测试 `getErrorMessage` 正确提取错误信息

### E2E 测试

- 测试 Toast 正确显示在 top-center 位置
- 测试 rich-colors 模式下不同类型消息的颜色正确
- 测试多个消息堆叠显示
- 测试消息自动关闭（4 秒后消失）
- 测试批量操作消息合并

## 验收标准

- ✅ 所有消息提醒都有 UI 展示（不再是 console 输出）
- ✅ 消息显示在 top-center 位置
- ✅ 不同类型消息有不同的背景色和图标
- ✅ 消息 4 秒后自动消失
- ✅ 最多同时显示 3 个消息
- ✅ 批量操作可合并消息
- ✅ 所有现有代码无需修改即可正常工作
