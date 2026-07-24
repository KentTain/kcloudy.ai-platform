<script setup lang="ts">
/**
 * 成员选择器组件
 */

import { onMounted, ref, watch } from "vue";
import { getMembers } from "../../api/member";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import type { LibraryMember } from "../../types";

const props = defineProps<{
  libraryId: string;
  modelValue?: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
}>();

const members = ref<LibraryMember[]>([]);
const loading = ref(false);
const selectedIds = ref<string[]>(props.modelValue ?? []);

const fetchMembers = async () => {
  loading.value = true;
  try {
    const response = await getMembers(props.libraryId, { page: 1, page_size: 100 });
    members.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    notifyError(getErrorMessage(error, "获取成员列表失败"));
  } finally {
    loading.value = false;
  }
};

const toggleMember = (userId: string) => {
  const idx = selectedIds.value.indexOf(userId);
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1);
  } else {
    selectedIds.value.push(userId);
  }
  emit("update:modelValue", selectedIds.value);
};

onMounted(() => {
  fetchMembers();
});

watch(() => props.libraryId, () => {
  fetchMembers();
});
</script>

<template>
  <div class="flex flex-col gap-1">
    <div v-if="loading" class="px-2 py-1 text-xs text-muted-foreground">加载中...</div>
    <label
      v-for="member in members"
      :key="member.id"
      class="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent cursor-pointer"
    >
      <input
        type="checkbox"
        :checked="selectedIds.includes(member.user_id)"
        @change="toggleMember(member.user_id)"
      />
      <span>{{ member.user_name }}</span>
      <span class="ml-auto text-xs text-muted-foreground">{{ member.role }}</span>
    </label>
  </div>
</template>
