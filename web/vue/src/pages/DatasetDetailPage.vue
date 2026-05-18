<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getDataset } from "@/api";
import type { Dataset } from "@/types";

const route = useRoute();
const router = useRouter();

const dataset = ref<Dataset | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const id = route.params.id as string;
  try {
    dataset.value = await getDataset(id);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "获取知识库详情失败";
  } finally {
    loading.value = false;
  }
});

// biome-ignore lint/correctness/noUnusedVariables: used in template
const goBack = () => {
  router.push("/datasets");
};
</script>

<template>
  <div class="p-8">
    <div class="mx-auto max-w-4xl">
      <div class="mb-6">
        <button class="text-blue-600 hover:underline" @click="goBack">← 返回列表</button>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="flex justify-center py-12">
        <AppLoading size="lg" />
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="rounded-lg bg-red-50 p-4">
        <p class="text-red-600">{{ error }}</p>
        <AppButton class="mt-2" @click="goBack">返回列表</AppButton>
      </div>

      <!-- Dataset detail -->
      <div v-else-if="dataset">
        <AppCard :title="dataset.name">
          <div class="space-y-4">
            <div>
              <label class="text-sm font-medium text-gray-500">描述</label>
              <p class="mt-1 text-gray-800">{{ dataset.description || "暂无描述" }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-500">ID</label>
              <p class="mt-1 font-mono text-sm text-gray-600">{{ dataset.id }}</p>
            </div>
            <div class="flex gap-2 pt-4">
              <AppButton>编辑</AppButton>
              <AppButton variant="secondary">删除</AppButton>
            </div>
          </div>
        </AppCard>
      </div>

      <!-- Not found -->
      <div v-else class="py-12 text-center">
        <p class="text-gray-500">知识库不存在</p>
      </div>
    </div>
  </div>
</template>