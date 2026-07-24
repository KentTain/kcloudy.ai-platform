<script setup lang="ts">
/**
 * 文件夹树浏览器组件
 */

import { onMounted, ref, watch } from "vue";
import { getFolders } from "../../api/folder";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import type { Folder } from "../../types";

const props = defineProps<{
  libraryId: string;
  modelValue?: string | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
}>();

const folders = ref<Folder[]>([]);
const loading = ref(false);
const expandedIds = ref<Set<string>>(new Set());

const fetchFolders = async () => {
  loading.value = true;
  try {
    const response = await getFolders({ library_id: props.libraryId, page: 1, page_size: 500 });
    folders.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    notifyError(getErrorMessage(error, "获取文件夹列表失败"));
  } finally {
    loading.value = false;
  }
};

const toggleExpand = (id: string) => {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id);
  } else {
    expandedIds.value.add(id);
  }
};

const selectFolder = (id: string | null) => {
  emit("update:modelValue", id);
};

const childFolders = (parentId: string | null) =>
  folders.value.filter((f) => f.parent_id === parentId);

onMounted(() => {
  fetchFolders();
});

watch(() => props.libraryId, () => {
  fetchFolders();
});
</script>

<template>
  <div class="flex flex-col gap-1">
    <button
      class="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent text-left"
      :class="{ 'bg-accent': modelValue === null }"
      @click="selectFolder(null)"
    >
      <span class="font-medium">全部文件</span>
    </button>

    <div v-if="loading" class="px-2 py-1 text-xs text-muted-foreground">加载中...</div>

    <template v-for="folder in childFolders(null)" :key="folder.id">
      <div class="pl-2">
        <button
          class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent text-left"
          :class="{ 'bg-accent': modelValue === folder.id }"
          @click="selectFolder(folder.id)"
        >
          <button
            v-if="!folder.tree_leaf"
            class="shrink-0 text-muted-foreground hover:text-foreground"
            @click.stop="toggleExpand(folder.id)"
          >
            <span class="text-xs">{{ expandedIds.has(folder.id) ? "▼" : "▶" }}</span>
          </button>
          <span class="shrink-0">📁</span>
          <span class="truncate">{{ folder.name }}</span>
        </button>

        <template v-if="expandedIds.has(folder.id)">
          <div v-for="child in childFolders(folder.id)" :key="child.id" class="pl-3">
            <button
              class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent text-left"
              :class="{ 'bg-accent': modelValue === child.id }"
              @click="selectFolder(child.id)"
            >
              <span class="shrink-0">📁</span>
              <span class="truncate">{{ child.name }}</span>
            </button>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>
