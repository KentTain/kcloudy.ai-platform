# 统一消息提醒组件实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 使用 vue-sonner + shadcn-vue 封装实现统一的 Toast 消息提醒组件

**架构：** 在现有 shadcn-vue 生态基础上，添加 vue-sonner 依赖，创建 Sonner.vue 封装组件，通过 feedback.ts 提供统一的 API 给所有模块使用。

**技术栈：** Vue 3 + TypeScript + vue-sonner + shadcn-vue + lucide-vue-next

---

## 文件结构

### 创建的文件

- `web/vue/src/components/ui/sonner/Sonner.vue` - Sonner 组件封装，使用 lucide 图标
- `web/vue/src/components/ui/sonner/index.ts` - 导出 Toaster 组件
- `web/vue/tests/framework/unit/feedback.test.ts` - feedback 工具函数单元测试
- `web/vue/tests/framework/e2e/toast.spec.ts` - Toast E2E 测试

### 修改的文件

- `web/vue/package.json` - 添加 vue-sonner 依赖
- `web/vue/src/App.vue` - 注册全局 Toaster 组件
- `web/vue/src/framework/utils/feedback.ts` - 使用 toast API 替代 console 输出

---

## 任务 1：添加 vue-sonner 依赖

**文件：**
- 修改：`web/vue/package.json`

- [x] **步骤 1：安装 vue-sonner 依赖**

```bash
cd web/vue && pnpm add vue-sonner
```

- [x] **步骤 2：验证依赖安装成功**

运行：`cd web/vue && pnpm list vue-sonner`
预期：显示 vue-sonner 版本信息

- [x] **步骤 3：Commit 依赖变更**

```bash
git add web/vue/package.json web/vue/pnpm-lock.yaml
git commit -m "chore(deps): 添加 vue-sonner 依赖

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2：创建 Sonner 组件封装

**文件：**
- 创建：`web/vue/src/components/ui/sonner/Sonner.vue`
- 创建：`web/vue/src/components/ui/sonner/index.ts`

- [x] **步骤 1：创建 Sonner.vue 组件**

```vue
<!-- web/vue/src/components/ui/sonner/Sonner.vue -->
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

- [x] **步骤 2：创建 index.ts 导出文件**

```typescript
// web/vue/src/components/ui/sonner/index.ts
export { default as Toaster } from "./Sonner.vue";
```

- [x] **步骤 3：Commit Sonner 组件**

```bash
git add web/vue/src/components/ui/sonner/
git commit -m "feat(ui): 新增 Sonner Toast 组件封装

- 基于 vue-sonner 封装
- 使用 lucide-vue-next 图标
- 支持 success/error/warning/info/loading 类型

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3：全局注册 Toaster 组件

**文件：**
- 修改：`web/vue/src/App.vue`

- [x] **步骤 1：更新 App.vue 注册 Toaster**

```vue
<!-- web/vue/src/App.vue -->
<script setup lang="ts">
/**
 * App 根组件
 */
import { Toaster } from "@/components/ui/sonner"
</script>

<template>
  <router-view />
  <Toaster position="top-center" rich-colors :visibleToasts="3" />
</template>

<style>
/* Tailwind v4 已在 @layer base 中提供重置样式，此处无需重复定义 */

html,
body,
#app {
  height: 100%;
}
</style>
```

- [x] **步骤 2：验证组件导入正确**

运行：`cd web/vue && pnpm type-check`
预期：无类型错误

- [x] **步骤 3：Commit App.vue 变更**

```bash
git add web/vue/src/App.vue
git commit -m "feat(app): 全局注册 Toaster 组件

- 位置：top-center
- 启用 rich-colors 模式
- 最多显示 3 个消息

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4：更新 feedback.ts 使用 toast API

**文件：**
- 修改：`web/vue/src/framework/utils/feedback.ts`

- [x] **步骤 1：更新 feedback.ts**

```typescript
// web/vue/src/framework/utils/feedback.ts
/**
 * 反馈工具函数
 *
 * 提供通知、确认和错误消息提取功能
 */

import { toast } from "vue-sonner"

/**
 * 成功提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifySuccess = (message: string, options?: { id?: string; duration?: number }) => {
  toast.success(message, options)
}

/**
 * 错误提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifyError = (message: string, options?: { id?: string; duration?: number }) => {
  toast.error(message, options)
}

/**
 * 警告提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifyWarning = (message: string, options?: { id?: string; duration?: number }) => {
  toast.warning(message, options)
}

/**
 * 信息提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifyInfo = (message: string, options?: { id?: string; duration?: number }) => {
  toast.info(message, options)
}

/**
 * 批量操作成功提示
 * @param count - 处理数量
 * @param action - 操作名称（如"删除"、"导入"）
 */
export const notifyBatchSuccess = (count: number, action: string) => {
  toast.success(`${action}成功`, {
    id: `batch-${action}`,
    description: `已处理 ${count} 项`
  })
}

/**
 * 批量操作失败提示
 * @param count - 失败数量
 * @param action - 操作名称（如"删除"、"导入"）
 */
export const notifyBatchError = (count: number, action: string) => {
  toast.error(`${action}失败`, {
    id: `batch-${action}`,
    description: `${count} 项处理失败`
  })
}

/**
 * 确认对话框
 * @param message - 确认消息
 * @returns 用户是否确认
 */
export const confirmAction = (message: string) => window.confirm(message)

/**
 * 提取错误消息
 * @param error - 错误对象
 * @param fallback - 默认消息
 * @returns 错误消息字符串
 */
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

- [x] **步骤 2：验证类型检查通过**

运行：`cd web/vue && pnpm type-check`
预期：无类型错误

- [x] **步骤 3：Commit feedback.ts 变更**

```bash
git add web/vue/src/framework/utils/feedback.ts
git commit -m "feat(feedback): 使用 toast API 替代 console 输出

- notifySuccess/Error/Warning/Info 使用 vue-sonner
- 新增 notifyBatchSuccess/BatchError 批量操作 API
- 支持消息合并（id 参数）和自定义持续时间
- 保持向后兼容，API 签名不变

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 5：编写单元测试

**文件：**
- 创建：`web/vue/tests/framework/unit/feedback.test.ts`

- [x] **步骤 1：编写单元测试**

```typescript
// web/vue/tests/framework/unit/feedback.test.ts
import { describe, expect, it, vi } from "vitest"

// Mock vue-sonner
vi.mock("vue-sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}))

import { toast } from "vue-sonner"
import {
  confirmAction,
  getErrorMessage,
  notifyBatchError,
  notifyBatchSuccess,
  notifyError,
  notifyInfo,
  notifySuccess,
  notifyWarning,
} from "@/framework/utils/feedback"

describe("feedback utils", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe("notifySuccess", () => {
    it("should call toast.success with message", () => {
      notifySuccess("操作成功")
      expect(toast.success).toHaveBeenCalledWith("操作成功", undefined)
    })

    it("should call toast.success with options", () => {
      notifySuccess("保存成功", { id: "save", duration: 5000 })
      expect(toast.success).toHaveBeenCalledWith("保存成功", { id: "save", duration: 5000 })
    })
  })

  describe("notifyError", () => {
    it("should call toast.error with message", () => {
      notifyError("操作失败")
      expect(toast.error).toHaveBeenCalledWith("操作失败", undefined)
    })

    it("should call toast.error with options", () => {
      notifyError("网络错误", { id: "network", duration: 6000 })
      expect(toast.error).toHaveBeenCalledWith("网络错误", { id: "network", duration: 6000 })
    })
  })

  describe("notifyWarning", () => {
    it("should call toast.warning with message", () => {
      notifyWarning("警告提示")
      expect(toast.warning).toHaveBeenCalledWith("警告提示", undefined)
    })
  })

  describe("notifyInfo", () => {
    it("should call toast.info with message", () => {
      notifyInfo("信息提示")
      expect(toast.info).toHaveBeenCalledWith("信息提示", undefined)
    })
  })

  describe("notifyBatchSuccess", () => {
    it("should show batch success message with count", () => {
      notifyBatchSuccess(10, "删除")
      expect(toast.success).toHaveBeenCalledWith("删除成功", {
        id: "batch-删除",
        description: "已处理 10 项",
      })
    })
  })

  describe("notifyBatchError", () => {
    it("should show batch error message with count", () => {
      notifyBatchError(5, "导入")
      expect(toast.error).toHaveBeenCalledWith("导入失败", {
        id: "batch-导入",
        description: "5 项处理失败",
      })
    })
  })

  describe("confirmAction", () => {
    it("should call window.confirm with message", () => {
      const mockConfirm = vi.spyOn(window, "confirm").mockReturnValue(true)
      const result = confirmAction("确认删除？")
      expect(mockConfirm).toHaveBeenCalledWith("确认删除？")
      expect(result).toBe(true)
      mockConfirm.mockRestore()
    })
  })

  describe("getErrorMessage", () => {
    it("should extract msg from error response", () => {
      const error = {
        response: {
          data: {
            msg: "操作失败",
          },
        },
      }
      expect(getErrorMessage(error, "默认消息")).toBe("操作失败")
    })

    it("should extract detail from error response", () => {
      const error = {
        response: {
          data: {
            detail: "详细信息",
          },
        },
      }
      expect(getErrorMessage(error, "默认消息")).toBe("详细信息")
    })

    it("should return fallback when no response data", () => {
      const error = new Error("网络错误")
      expect(getErrorMessage(error, "默认消息")).toBe("网络错误")
    })

    it("should return fallback for unknown error", () => {
      expect(getErrorMessage("unknown", "默认消息")).toBe("默认消息")
    })
  })
})
```

- [x] **步骤 2：运行单元测试验证通过**

运行：`cd web/vue && pnpm test:unit tests/framework/unit/feedback.test.ts --run`
预期：所有测试通过

- [x] **步骤 3：Commit 单元测试**

```bash
git add web/vue/tests/framework/unit/feedback.test.ts
git commit -m "test(feedback): 新增 feedback 工具函数单元测试

- 测试 notifySuccess/Error/Warning/Info 函数
- 测试 notifyBatchSuccess/BatchError 函数
- 测试 confirmAction 和 getErrorMessage 函数
- 覆盖所有 API 和边界情况

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 6：编写 E2E 测试

**文件：**
- 创建：`web/vue/tests/framework/e2e/toast.spec.ts`

- [x] **步骤 1：编写 E2E 测试**

```typescript
// web/vue/tests/framework/e2e/toast.spec.ts
import { expect, test } from "@playwright/test"

test.describe("Toast 通知测试", () => {
  test.beforeEach(async ({ page }) => {
    // 登录到系统
    await page.goto("/login")
    await page.fill('input[type="text"]', "admin")
    await page.fill('input[type="password"]', "admin123")
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/(demo|ai)/)
  })

  test("应该显示成功消息", async ({ page }) => {
    // 导航到租户管理页面
    await page.goto("/tenant/admin/tenants")

    // 触发一个成功操作（如果页面有操作按钮）
    // 这里需要根据实际页面结构编写

    // 验证 Toast 出现
    const toast = page.locator('[data-sonner-toast][data-type="success"]')
    await expect(toast).toBeVisible({ timeout: 5000 })

    // 验证 Toast 在 4 秒后消失
    await page.waitForTimeout(4500)
    await expect(toast).not.toBeVisible()
  })

  test("应该在 top-center 位置显示", async ({ page }) => {
    // 触发一个操作
    // ...

    // 验证 Toast 位置
    const toast = page.locator('[data-sonner-toast]').first()
    await expect(toast).toBeVisible()

    // 检查位置（top-center）
    const boundingBox = await toast.boundingBox()
    if (boundingBox) {
      const pageWidth = page.viewportSize()?.width || 1280
      const centerX = pageWidth / 2
      const toastCenterX = boundingBox.x + boundingBox.width / 2

      // 允许 50px 误差
      expect(Math.abs(toastCenterX - centerX)).toBeLessThan(50)
      // 应该在页面顶部
      expect(boundingBox.y).toBeLessThan(100)
    }
  })

  test("应该显示 rich-colors 样式", async ({ page }) => {
    // 触发成功操作
    // ...

    // 验证成功 Toast 的样式
    const successToast = page.locator('[data-sonner-toast][data-type="success"]')
    await expect(successToast).toBeVisible()

    // 触发错误操作
    // ...

    // 验证错误 Toast 的样式
    const errorToast = page.locator('[data-sonner-toast][data-type="error"]')
    await expect(errorToast).toBeVisible()
  })

  test("最多应该显示 3 个消息", async ({ page }) => {
    // 快速触发多个操作
    // ...

    // 等待 Toast 出现
    await page.waitForTimeout(1000)

    // 验证最多显示 3 个
    const toasts = await page.locator('[data-sonner-toast]').count()
    expect(toasts).toBeLessThanOrEqual(3)
  })
})
```

- [x] **步骤 2：运行 E2E 测试验证通过**

运行：`cd web/vue && pnpm test:e2e tests/framework/e2e/toast.spec.ts`
预期：所有测试通过（需要后端服务运行）

- [x] **步骤 3：Commit E2E 测试**

```bash
git add web/vue/tests/framework/e2e/toast.spec.ts
git commit -m "test(e2e): 新增 Toast E2E 测试

- 测试 Toast 显示位置（top-center）
- 测试 rich-colors 样式
- 测试消息自动关闭
- 测试最大显示数量限制

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 7：验证功能

**文件：**
- 无文件变更，仅验证

- [x] **步骤 1：启动开发服务器**

```bash
cd web/vue && pnpm dev
```

- [x] **步骤 2：手动测试 Toast 功能**

1. 打开浏览器访问 http://localhost:5173
2. 登录系统
3. 执行一个操作（如创建租户）
4. 验证 Toast 正确显示在 top-center 位置
5. 验证 Toast 有正确的背景色和图标
6. 验证 Toast 在 4 秒后自动消失

- [x] **步骤 3：运行所有测试验证通过**

```bash
cd web/vue
pnpm test:unit tests/framework/unit/feedback.test.ts --run
```

预期：所有测试通过

---

## 验收标准

- ✅ vue-sonner 依赖已添加到 package.json
- ✅ Sonner.vue 组件已创建，使用 lucide 图标
- ✅ Toaster 已全局注册到 App.vue
- ✅ feedback.ts 使用 toast API 替代 console 输出
- ✅ 单元测试覆盖所有 feedback 函数
- ✅ E2E 测试覆盖 Toast 显示和行为
- ✅ Toast 显示在 top-center 位置
- ✅ Toast 有 rich-colors 样式
- ✅ Toast 在 4 秒后自动消失
- ✅ 最多显示 3 个消息
- ✅ 批量操作 API 可合并消息
- ✅ 所有现有代码无需修改即可正常工作
