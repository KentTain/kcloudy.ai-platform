<script setup lang="ts">
import { onMounted, ref } from "vue";
// biome-ignore lint/correctness/noUnusedImports: used in template
import AppModal from "@/components/ui/AppModal.vue";
import { useModal } from "@/composables/useModal";
import { useDatasetsStore } from "@/stores/datasets";
import type { CreateDatasetRequest } from "@/types";

const store = useDatasetsStore();
const modal = useModal();
// biome-ignore lint/correctness/noUnusedVariables: used in template
const { isOpen, open, close } = modal;

const form = ref<CreateDatasetRequest>({ name: "", description: "" });
const submitting = ref(false);
const message = ref<string | null>(null);
const messageType = ref<"success" | "error">("success");

onMounted(() => {
  store.fetchDatasets();
});

// biome-ignore lint/correctness/noUnusedVariables: used in template
const handleSubmit = () => {
  if (!form.value.name.trim()) return;

  submitting.value = true;
  message.value = null;

  store
    .createDataset(form.value)
    .then(() => {
      message.value = "知识库已创建";
      messageType.value = "success";
      resetForm();
      close();
      setTimeout(() => {
        message.value = null;
      }, 3000);
    })
    .catch((e: unknown) => {
      message.value = e instanceof Error ? e.message : "创建知识库失败";
      messageType.value = "error";
    })
    .finally(() => {
      submitting.value = false;
    });
};

function resetForm() {
  form.value = { name: "", description: "" };
}

// biome-ignore lint/correctness/noUnusedVariables: used in template
const handleClose = () => {
  resetForm();
  close();
};
</script>

<template>
  <div class="p-8">
    <div class="mx-auto max-w-4xl">
      <div class="mb-8 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-800">知识库列表</h1>
        <AppButton @click="open">创建知识库</AppButton>
      </div>

      <!-- Message -->
      <div
        v-if="message"
        :class="[
          'mb-4 rounded-lg px-4 py-2 text-sm font-medium',
          messageType === 'success'
            ? 'bg-green-50 text-green-700'
            : 'bg-red-50 text-red-700',
        ]"
      >
        {{ message }}
      </div>

      <!-- Loading state -->
      <div v-if="store.loading" class="flex justify-center py-12">
        <AppLoading size="lg" />
      </div>

      <!-- Error state -->
      <div v-else-if="store.error" class="rounded-lg bg-red-50 p-4">
        <p class="text-red-600">{{ store.error }}</p>
        <AppButton class="mt-2" @click="store.fetchDatasets">重试</AppButton>
      </div>

      <!-- Empty state -->
      <div v-else-if="store.datasets.length === 0" class="py-12 text-center">
        <p class="text-gray-500">暂无知识库，点击上方按钮创建。</p>
      </div>

      <!-- Dataset list -->
      <div v-else class="grid grid-cols-1 gap-4">
        <RouterLink
          v-for="dataset in store.datasets"
          :key="dataset.id"
          :to="`/datasets/${dataset.id}`"
        >
          <AppCard class="cursor-pointer transition-shadow hover:shadow-md">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-semibold text-gray-800">{{ dataset.name }}</h3>
                <p class="mt-1 text-sm text-gray-500">
                  {{ dataset.description || "暂无描述" }}
                </p>
              </div>
              <span class="text-gray-400">→</span>
            </div>
          </AppCard>
        </RouterLink>
      </div>
    </div>

    <!-- Create Dataset Modal -->
    <AppModal :open="isOpen" title="创建知识库" @close="handleClose">
      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <div>
            <label for="dataset-name" class="mb-1 block text-sm font-medium text-gray-700">
              名称 <span class="text-red-500">*</span>
            </label>
            <input
              id="dataset-name"
              v-model="form.name"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="请输入知识库名称"
              :disabled="submitting"
            />
          </div>
          <div>
            <label for="dataset-desc" class="mb-1 block text-sm font-medium text-gray-700">
              描述
            </label>
            <textarea
              id="dataset-desc"
              v-model="form.description"
              rows="3"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="请输入知识库描述（选填）"
              :disabled="submitting"
            />
          </div>
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" :disabled="submitting" @click="handleClose">
            取消
          </AppButton>
          <AppButton :disabled="submitting || !form.name.trim()" @click="handleSubmit">
            {{ submitting ? "创建中..." : "创建" }}
          </AppButton>
        </div>
      </template>
    </AppModal>
  </div>
</template>