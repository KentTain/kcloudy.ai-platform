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
