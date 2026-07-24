<script setup lang="ts">
/**
 * 标签选择器组件
 */

import { onMounted, ref } from "vue";
import { getTags } from "../../api/tag";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import { Badge } from "@/components";
import type { Tag } from "../../types";

const props = defineProps<{
  modelValue?: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
}>();

const tags = ref<Tag[]>([]);
const loading = ref(false);
const selectedIds = ref<string[]>(props.modelValue ?? []);

const fetchTags = async () => {
  loading.value = true;
  try {
    const response = await getTags({ page: 1, page_size: 500 });
    tags.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    notifyError(getErrorMessage(error, "获取标签列表失败"));
  } finally {
    loading.value = false;
  }
};

const toggleTag = (tagId: string) => {
  const idx = selectedIds.value.indexOf(tagId);
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1);
  } else {
    selectedIds.value.push(tagId);
  }
  emit("update:modelValue", selectedIds.value);
};

onMounted(() => {
  fetchTags();
});
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <div v-if="loading" class="text-sm text-muted-foreground">加载中...</div>
    <button
      v-for="tag in tags"
      :key="tag.id"
      @click="toggleTag(tag.id)"
    >
      <Badge
        :variant="selectedIds.includes(tag.id) ? 'default' : 'outline'"
        class="cursor-pointer"
      >
        {{ tag.name }}
      </Badge>
    </button>
    <span v-if="!loading && tags.length === 0" class="text-sm text-muted-foreground">暂无标签</span>
  </div>
</template>
