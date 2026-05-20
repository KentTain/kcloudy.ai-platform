# Demo 模块实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 web/vue/src/demo/ 下实现测试示例模块，提供 API 连通性测试和 UI 组件交互测试的仪表盘页面。

**架构：** 单路由 `/demo` + 三个标签页切换。`useApiTest` composable 封装 API 测试状态管理，两个子组件分别渲染 API 测试和组件交互标签页内容，扩展预留标签页内联在主页面中。

**技术栈：** Vue 3.5 + TypeScript + Pinia + Tailwind CSS v4 + Vitest

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `src/demo/types/index.ts` | 创建 | ApiTestResult 类型定义 |
| `src/demo/composables/useApiTest.ts` | 创建 | API 测试请求状态管理 |
| `src/demo/components/ApiTestPanel.vue` | 创建 | API 测试标签页内容 |
| `src/demo/components/ComponentTestPanel.vue` | 创建 | 组件交互标签页内容 |
| `src/demo/pages/DemoPage.vue` | 创建 | 主页面，标签切换 + 扩展预留标签 |
| `src/router/index.ts` | 修改 | 添加 `/demo` 路由 |
| `tests/demo/composables/useApiTest.test.ts` | 创建 | useApiTest 单元测试 |

---

### 任务 1：定义 demo 类型

**文件：**
- 创建：`src/demo/types/index.ts`
- 测试：`tests/demo/composables/useApiTest.test.ts`（任务 2 中使用）

- [ ] **步骤 1：创建类型定义文件**

```typescript
// src/demo/types/index.ts
export type ApiTestStatus = "idle" | "loading" | "success" | "error";

export interface ApiTestResult {
  status: ApiTestStatus;
  data: unknown;
  error: string | null;
  duration: number | null;
}
```

- [ ] **步骤 2：Commit**

```bash
git add src/demo/types/index.ts
git commit -m "feat(demo): add ApiTestResult type definition"
```

---

### 任务 2：实现 useApiTest composable

**文件：**
- 创建：`src/demo/composables/useApiTest.ts`
- 测试：`tests/demo/composables/useApiTest.test.ts`

- [ ] **步骤 1：编写失败的测试**

```typescript
// tests/demo/composables/useApiTest.test.ts
import { describe, expect, it, vi } from "vitest";
import { useApiTest } from "@/demo/composables/useApiTest";

describe("useApiTest", () => {
  it("initializes with idle status", () => {
    const { result } = useApiTest();
    expect(result.value.status).toBe("idle");
    expect(result.value.data).toBeNull();
    expect(result.value.error).toBeNull();
    expect(result.value.duration).toBeNull();
  });

  it("sets status to success and captures data on successful execute", async () => {
    const mockFn = vi.fn().mockResolvedValue({ status: "ok" });
    const { result, execute } = useApiTest(mockFn);

    await execute();

    expect(result.value.status).toBe("success");
    expect(result.value.data).toEqual({ status: "ok" });
    expect(result.value.error).toBeNull();
    expect(result.value.duration).toBeGreaterThanOrEqual(0);
  });

  it("sets status to error and captures error message on failed execute", async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error("Network error"));
    const { result, execute } = useApiTest(mockFn);

    await execute();

    expect(result.value.status).toBe("error");
    expect(result.value.data).toBeNull();
    expect(result.value.error).toBe("Network error");
    expect(result.value.duration).toBeGreaterThanOrEqual(0);
  });

  it("uses default error message for non-Error rejections", async () => {
    const mockFn = vi.fn().mockRejectedValue("string error");
    const { result, execute } = useApiTest(mockFn);

    await execute();

    expect(result.value.error).toBe("请求失败");
  });

  it("sets status to loading during execution", async () => {
    let resolvePromise: (value: unknown) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    const mockFn = vi.fn().mockReturnValue(promise);
    const { result, execute } = useApiTest(mockFn);

    const execPromise = execute();
    expect(result.value.status).toBe("loading");

    resolvePromise!({ ok: true });
    await execPromise;

    expect(result.value.status).toBe("success");
  });

  it("reset() returns result to idle state", async () => {
    const mockFn = vi.fn().mockResolvedValue({ ok: true });
    const { result, execute, reset } = useApiTest(mockFn);

    await execute();
    expect(result.value.status).toBe("success");

    reset();

    expect(result.value.status).toBe("idle");
    expect(result.value.data).toBeNull();
    expect(result.value.error).toBeNull();
    expect(result.value.duration).toBeNull();
  });
});
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd web/vue && pnpm test:unit -- --run tests/demo/composables/useApiTest.test.ts`
预期：FAIL，报错 "Cannot find module '@/demo/composables/useApiTest'"

- [ ] **步骤 3：实现 useApiTest**

```typescript
// src/demo/composables/useApiTest.ts
import { ref } from "vue";
import type { ApiTestResult } from "../types";

export function useApiTest(apiFn?: () => Promise<unknown>) {
  const result = ref<ApiTestResult>({
    status: "idle",
    data: null,
    error: null,
    duration: null,
  });

  async function execute(fn?: () => Promise<unknown>) {
    const fnToCall = fn ?? apiFn;
    if (!fnToCall) return;

    result.value = { status: "loading", data: null, error: null, duration: null };
    const start = performance.now();

    try {
      const data = await fnToCall();
      const duration = performance.now() - start;
      result.value = { status: "success", data, error: null, duration };
    } catch (e: unknown) {
      const duration = performance.now() - start;
      const error = e instanceof Error ? e.message : "请求失败";
      result.value = { status: "error", data: null, error, duration };
    }
  }

  function reset() {
    result.value = { status: "idle", data: null, error: null, duration: null };
  }

  return { result, execute, reset };
}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd web/vue && pnpm test:unit -- --run tests/demo/composables/useApiTest.test.ts`
预期：PASS，所有 6 个测试通过

- [ ] **步骤 5：Commit**

```bash
git add src/demo/composables/useApiTest.ts tests/demo/composables/useApiTest.test.ts
git commit -m "feat(demo): add useApiTest composable with tests"
```

---

### 任务 3：实现 ApiTestPanel 组件

**文件：**
- 创建：`src/demo/components/ApiTestPanel.vue`

- [ ] **步骤 1：实现 ApiTestPanel**

该组件渲染 5 个 API 测试卡片。复用 `src/api/` 中已有的 `checkHealth`、`getDatasets`、`createDataset`、`deleteDataset` 函数和 `src/components/ui/` 的 UI 组件。

```vue
<!-- src/demo/components/ApiTestPanel.vue -->
<script setup lang="ts">
import { ref } from "vue";
import AppButton from "@/components/ui/AppButton.vue";
import AppCard from "@/components/ui/AppCard.vue";
import AppLoading from "@/components/ui/AppLoading.vue";
import AppModal from "@/components/ui/AppModal.vue";
import { useModal } from "@/composables/useModal";
import { checkHealth, createDataset, deleteDataset, getDatasets } from "@/api";
import { useApiTest } from "../composables/useApiTest";

const healthTest = useApiTest(() => checkHealth());
const listTest = useApiTest(() => getDatasets());

const createModal = useModal();
const createForm = ref({ name: "", description: "" });
const createTest = useApiTest();

const handleSubmitCreate = async () => {
  if (!createForm.value.name.trim()) return;
  await createTest.execute(() => createDataset(createForm.value));
  if (createTest.result.value.status === "success") {
    createForm.value = { name: "", description: "" };
    createModal.close();
  }
};

const deleteId = ref("");
const deleteTest = useApiTest();

const handleDelete = async () => {
  if (!deleteId.value.trim()) return;
  await deleteTest.execute(() => deleteDataset(deleteId.value.trim()));
  if (deleteTest.result.value.status === "success") {
    deleteId.value = "";
  }
};

function formatResult(result: { status: string; data: unknown; error: string | null; duration: number | null }) {
  if (result.status === "idle") return null;
  if (result.status === "loading") return null;
  if (result.status === "error") return result.error;
  return JSON.stringify(result.data, null, 2);
}

function statusColor(status: string) {
  if (status === "success") return "text-green-600";
  if (status === "error") return "text-red-600";
  if (status === "loading") return "text-blue-600";
  return "text-gray-400";
}
</script>

<template>
  <div class="space-y-4">
    <!-- 健康检查 -->
    <AppCard title="健康检查 — GET /health">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <p class="mb-2 text-sm text-gray-500">测试后端服务是否正常运行</p>
          <div v-if="healthTest.result.value.status === 'loading'" class="py-2">
            <AppLoading size="sm" />
          </div>
          <p v-if="healthTest.result.value.duration !== null" class="text-xs text-gray-400">
            耗时：{{ healthTest.result.value.duration.toFixed(0) }}ms
          </p>
          <p :class="['text-sm font-medium', statusColor(healthTest.result.value.status)]">
            {{ healthTest.result.value.status === 'idle' ? '' : healthTest.result.value.status }}
          </p>
          <pre v-if="formatResult(healthTest.result.value)" class="mt-2 max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs">{{ formatResult(healthTest.result.value) }}</pre>
        </div>
        <AppButton @click="healthTest.execute()">发送</AppButton>
      </div>
    </AppCard>

    <!-- 知识库列表 -->
    <AppCard title="知识库列表 — GET /v1/datasets">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <p class="mb-2 text-sm text-gray-500">获取所有知识库</p>
          <div v-if="listTest.result.value.status === 'loading'" class="py-2">
            <AppLoading size="sm" />
          </div>
          <p v-if="listTest.result.value.duration !== null" class="text-xs text-gray-400">
            耗时：{{ listTest.result.value.duration.toFixed(0) }}ms
          </p>
          <p :class="['text-sm font-medium', statusColor(listTest.result.value.status)]">
            {{ listTest.result.value.status === 'idle' ? '' : listTest.result.value.status }}
          </p>
          <pre v-if="formatResult(listTest.result.value)" class="mt-2 max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs">{{ formatResult(listTest.result.value) }}</pre>
        </div>
        <AppButton @click="listTest.execute()">发送</AppButton>
      </div>
    </AppCard>

    <!-- 创建知识库 -->
    <AppCard title="创建知识库 — POST /v1/datasets">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <p class="mb-2 text-sm text-gray-500">通过表单提交创建新知识库</p>
          <p v-if="createTest.result.value.duration !== null" class="text-xs text-gray-400">
            耗时：{{ createTest.result.value.duration.toFixed(0) }}ms
          </p>
          <p :class="['text-sm font-medium', statusColor(createTest.result.value.status)]">
            {{ createTest.result.value.status === 'idle' ? '' : createTest.result.value.status }}
          </p>
          <pre v-if="formatResult(createTest.result.value)" class="mt-2 max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs">{{ formatResult(createTest.result.value) }}</pre>
        </div>
        <AppButton @click="createModal.open()">创建</AppButton>
      </div>
    </AppCard>

    <!-- 删除知识库 -->
    <AppCard title="删除知识库 — DELETE /v1/datasets/:id">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <p class="mb-2 text-sm text-gray-500">输入知识库 ID 进行删除</p>
          <div v-if="deleteTest.result.value.status === 'loading'" class="py-2">
            <AppLoading size="sm" />
          </div>
          <p v-if="deleteTest.result.value.duration !== null" class="text-xs text-gray-400">
            耗时：{{ deleteTest.result.value.duration.toFixed(0) }}ms
          </p>
          <p :class="['text-sm font-medium', statusColor(deleteTest.result.value.status)]">
            {{ deleteTest.result.value.status === 'idle' ? '' : deleteTest.result.value.status }}
          </p>
          <pre v-if="formatResult(deleteTest.result.value)" class="mt-2 max-h-40 overflow-auto rounded bg-gray-50 p-2 text-xs">{{ formatResult(deleteTest.result.value) }}</pre>
        </div>
        <div class="flex gap-2">
          <input
            v-model="deleteId"
            type="text"
            placeholder="输入 ID"
            class="w-28 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <AppButton :disabled="!deleteId.trim()" @click="handleDelete">删除</AppButton>
        </div>
      </div>
    </AppCard>

    <!-- AI 对话（预留） -->
    <AppCard title="AI 对话 — POST /v1/chat">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <p class="mb-2 text-sm text-gray-500">与 AI 助手进行对话</p>
          <p class="text-sm text-gray-400">即将支持</p>
        </div>
        <AppButton disabled>发送</AppButton>
      </div>
    </AppCard>

    <!-- 创建知识库弹窗 -->
    <AppModal :open="createModal.isOpen.value" title="创建知识库" @close="createModal.close()">
      <form @submit.prevent="handleSubmitCreate">
        <div class="space-y-4">
          <div>
            <label for="demo-dataset-name" class="mb-1 block text-sm font-medium text-gray-700">
              名称 <span class="text-red-500">*</span>
            </label>
            <input
              id="demo-dataset-name"
              v-model="createForm.name"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="请输入知识库名称"
            />
          </div>
          <div>
            <label for="demo-dataset-desc" class="mb-1 block text-sm font-medium text-gray-700">描述</label>
            <textarea
              id="demo-dataset-desc"
              v-model="createForm.description"
              rows="3"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="请输入知识库描述（选填）"
            />
          </div>
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" @click="createModal.close()">取消</AppButton>
          <AppButton :disabled="!createForm.name.trim()" @click="handleSubmitCreate">
            {{ createTest.result.value.status === 'loading' ? '创建中...' : '创建' }}
          </AppButton>
        </div>
      </template>
    </AppModal>
  </div>
</template>
```

- [ ] **步骤 2：运行 Biome 检查**

运行：`cd web/vue && pnpm check:fix`
预期：无错误

- [ ] **步骤 3：Commit**

```bash
git add src/demo/components/ApiTestPanel.vue
git commit -m "feat(demo): add ApiTestPanel component"
```

---

### 任务 4：实现 ComponentTestPanel 组件

**文件：**
- 创建：`src/demo/components/ComponentTestPanel.vue`

- [ ] **步骤 1：实现 ComponentTestPanel**

```vue
<!-- src/demo/components/ComponentTestPanel.vue -->
<script setup lang="ts">
import { ref } from "vue";
import AppButton from "@/components/ui/AppButton.vue";
import AppCard from "@/components/ui/AppCard.vue";
import AppLoading from "@/components/ui/AppLoading.vue";
import AppModal from "@/components/ui/AppModal.vue";
import { useModal } from "@/composables/useModal";

// AppButton 测试状态
const clickCount = ref(0);
const buttonVariant = ref<"primary" | "secondary">("primary");
const buttonDisabled = ref(false);

// AppCard 测试状态
const showCardTitle = ref(true);
const cardContentIndex = ref(0);
const cardContents = ["内容 A", "内容 B", "内容 C"];

// AppModal 测试状态
const modal = useModal();
const modalSubmitCount = ref(0);

// AppLoading 测试状态
const loadingSize = ref<"sm" | "md" | "lg">("md");
</script>

<template>
  <div class="space-y-4">
    <!-- AppButton -->
    <AppCard title="AppButton 按钮">
      <div class="space-y-3">
        <div class="flex items-center gap-4">
          <AppButton :variant="buttonVariant" :disabled="buttonDisabled" @click="clickCount++">
            点击我
          </AppButton>
          <AppButton variant="secondary" :disabled="buttonDisabled" @click="clickCount++">
            次要按钮
          </AppButton>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1">
            <input v-model="buttonVariant" type="radio" value="primary" /> primary
          </label>
          <label class="flex items-center gap-1">
            <input v-model="buttonVariant" type="radio" value="secondary" /> secondary
          </label>
          <label class="flex items-center gap-1">
            <input v-model="buttonDisabled" type="checkbox" /> disabled
          </label>
        </div>
        <p class="text-sm text-gray-500">点击次数：{{ clickCount }}</p>
      </div>
    </AppCard>

    <!-- AppCard -->
    <AppCard title="AppCard 卡片">
      <div class="space-y-3">
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1">
            <input v-model="showCardTitle" type="checkbox" /> 显示标题
          </label>
          <AppButton size="sm" @click="cardContentIndex = (cardContentIndex + 1) % cardContents.length">
            切换内容
          </AppButton>
        </div>
        <div class="rounded-lg border border-dashed border-gray-300 p-4">
          <AppCard :title="showCardTitle ? '卡片标题' : ''">
            <p class="text-sm text-gray-600">{{ cardContents[cardContentIndex] }}</p>
          </AppCard>
        </div>
      </div>
    </AppCard>

    <!-- AppModal -->
    <AppCard title="AppModal 弹窗">
      <div class="space-y-3">
        <AppButton @click="modal.open()">打开弹窗</AppButton>
        <p class="text-sm text-gray-500">弹窗提交次数：{{ modalSubmitCount }}</p>
      </div>
    </AppCard>

    <AppModal :open="modal.isOpen.value" title="测试弹窗" @close="modal.close()">
      <p class="text-sm text-gray-600">这是一个测试弹窗，点击提交会增加计数。</p>
      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" @click="modal.close()">取消</AppButton>
          <AppButton @click="modalSubmitCount++; modal.close()">提交</AppButton>
        </div>
      </template>
    </AppModal>

    <!-- AppLoading -->
    <AppCard title="AppLoading 加载">
      <div class="space-y-3">
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1">
            <input v-model="loadingSize" type="radio" value="sm" /> sm
          </label>
          <label class="flex items-center gap-1">
            <input v-model="loadingSize" type="radio" value="md" /> md
          </label>
          <label class="flex items-center gap-1">
            <input v-model="loadingSize" type="radio" value="lg" /> lg
          </label>
        </div>
        <div class="rounded-lg border border-dashed border-gray-300 p-4">
          <AppLoading :size="loadingSize" />
        </div>
      </div>
    </AppCard>
  </div>
</template>
```

注意：`AppButton` 目前不支持 `size` prop，卡片测试中的"切换内容"按钮需去掉 `size` 属性，使用默认样式。

修正：将 `<AppButton size="sm" @click="...">` 改为 `<AppButton @click="...">`。

- [ ] **步骤 2：运行 Biome 检查**

运行：`cd web/vue && pnpm check:fix`
预期：无错误

- [ ] **步骤 3：Commit**

```bash
git add src/demo/components/ComponentTestPanel.vue
git commit -m "feat(demo): add ComponentTestPanel component"
```

---

### 任务 5：实现 DemoPage 主页面

**文件：**
- 创建：`src/demo/pages/DemoPage.vue`

- [ ] **步骤 1：实现 DemoPage**

```vue
<!-- src/demo/pages/DemoPage.vue -->
<script setup lang="ts">
import { ref } from "vue";
import ApiTestPanel from "../components/ApiTestPanel.vue";
import ComponentTestPanel from "../components/ComponentTestPanel.vue";

type TabKey = "api" | "component" | "extend";

const activeTab = ref<TabKey>("api");

const tabs: { key: TabKey; label: string }[] = [
  { key: "api", label: "API 测试" },
  { key: "component", label: "组件交互" },
  { key: "extend", label: "扩展预留" },
];
</script>

<template>
  <div class="p-8">
    <div class="mx-auto max-w-4xl">
      <h1 class="mb-6 text-2xl font-bold text-gray-800">Demo 测试面板</h1>

      <!-- 标签栏 -->
      <div class="mb-6 flex border-b border-gray-200">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            activeTab === tab.key
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-500 hover:text-gray-700',
          ]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 标签内容 -->
      <ApiTestPanel v-if="activeTab === 'api'" />
      <ComponentTestPanel v-else-if="activeTab === 'component'" />

      <!-- 扩展预留 -->
      <div v-else-if="activeTab === 'extend'" class="py-12 text-center">
        <p class="mb-4 text-gray-500">更多测试功能开发中</p>
        <ul class="mx-auto inline-block space-y-2 text-left text-sm text-gray-400">
          <li>• WebSocket 连接测试</li>
          <li>• 流式响应（SSE）测试</li>
          <li>• 文件上传测试</li>
          <li>• 权限认证测试</li>
        </ul>
      </div>
    </div>
  </div>
</template>
```

- [ ] **步骤 2：运行 Biome 检查**

运行：`cd web/vue && pnpm check:fix`
预期：无错误

- [ ] **步骤 3：Commit**

```bash
git add src/demo/pages/DemoPage.vue
git commit -m "feat(demo): add DemoPage with tab switching"
```

---

### 任务 6：添加路由配置

**文件：**
- 修改：`src/router/index.ts`

- [ ] **步骤 1：在路由配置中添加 /demo 路由**

在 `src/router/index.ts` 的 `children` 数组中，`datasets/:id` 路由之后添加：

```typescript
{
  path: "demo",
  name: "Demo",
  component: () => import("@/demo/pages/DemoPage.vue"),
  meta: {
    title: "Demo 测试面板",
  },
},
```

- [ ] **步骤 2：在 HomePage 添加 Demo 入口链接**

修改 `src/pages/HomePage.vue`，在"快速开始"卡片的按钮区域添加一个跳转链接：

将：
```html
<AppButton variant="secondary">了解更多</AppButton>
```
替换为：
```html
<RouterLink to="/demo">
  <AppButton variant="secondary">Demo 面板</AppButton>
</RouterLink>
```

- [ ] **步骤 3：运行类型检查**

运行：`cd web/vue && pnpm type-check`
预期：无错误

- [ ] **步骤 4：Commit**

```bash
git add src/router/index.ts src/pages/HomePage.vue
git commit -m "feat(demo): add /demo route and home page link"
```

---

### 任务 7：验证与最终检查

- [ ] **步骤 1：运行全部单元测试**

运行：`cd web/vue && pnpm test:unit -- --run`
预期：所有测试通过

- [ ] **步骤 2：运行 Biome 全量检查**

运行：`cd web/vue && pnpm check`
预期：无错误

- [ ] **步骤 3：运行类型检查**

运行：`cd web/vue && pnpm type-check`
预期：无错误

- [ ] **步骤 4：启动开发服务器验证页面**

运行：`cd web/vue && pnpm dev`
手动验证：
- 访问 `/demo` 页面加载正常
- 三个标签页切换正常
- API 测试标签页各卡片布局正确
- 组件交互标签页各测试区交互正常
- 扩展预留标签页显示占位内容
- 首页"Demo 面板"按钮跳转正常
