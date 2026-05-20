<!-- src/demo/components/ApiTestPanel.vue -->
<script setup lang="ts">
import { ref } from "vue";
import { checkHealth, createDataset, deleteDataset, getDatasets } from "@/api";
import AppButton from "@/components/ui/AppButton.vue";
import AppCard from "@/components/ui/AppCard.vue";
import AppLoading from "@/components/ui/AppLoading.vue";
import AppModal from "@/components/ui/AppModal.vue";
import { useModal } from "@/composables/useModal";
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

function formatResult(result: {
  status: string;
  data: unknown;
  error: string | null;
  duration: number | null;
}) {
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
