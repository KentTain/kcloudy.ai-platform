<script setup lang="ts">
/**
 * 文件详情查看组件
 */

import { computed, onMounted, ref } from "vue";
import { getDocument } from "../../api/document";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import { Button, DescriptionList, type DescriptionItem } from "@/components";
import type { Document } from "../../types";

const props = defineProps<{
  documentId: string;
}>();

const document = ref<Document | null>(null);
const loading = ref(false);

const fetchDocument = async () => {
  loading.value = true;
  try {
    const response = await getDocument(props.documentId);
    document.value = response.data ?? null;
  } catch (error) {
    notifyError(getErrorMessage(error, "获取文档详情失败"));
  } finally {
    loading.value = false;
  }
};

const descriptionItems = computed<DescriptionItem[]>(() => {
  if (!document.value) return [];
  const doc = document.value;
  return [
    { label: "名称", value: doc.name },
    { label: "类型", value: doc.document_type },
    { label: "状态", value: doc.lifecycle_status },
    { label: "处理状态", value: doc.processing_status },
    { label: "文件大小", value: `${(doc.file_size / 1024).toFixed(1)} KB` },
    { label: "MIME 类型", value: doc.mime_type ?? "-" },
    { label: "创建时间", value: new Date(doc.created_at).toLocaleString() },
  ];
});

onMounted(() => {
  fetchDocument();
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <div v-if="loading" class="flex flex-col gap-3">
      <div v-for="n in 5" :key="n" class="h-5 w-full animate-pulse rounded bg-muted" />
    </div>
    <DescriptionList v-else :items="descriptionItems" :columns="2" bordered />
  </div>
</template>
