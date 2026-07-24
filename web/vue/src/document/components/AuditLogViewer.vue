<script setup lang="ts">
/**
 * 审计日志查看组件
 */

import { onMounted, ref } from "vue";
import { get } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";

const props = defineProps<{
  libraryId: string;
}>();

interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  operator_id: string;
  detail: string | null;
  created_at: string;
}

const logs = ref<AuditLog[]>([]);
const loading = ref(false);

const fetchLogs = async () => {
  loading.value = true;
  try {
    const response = await get<ApiResponse<AuditLog[]>>(
      `/document/console/v1/libraries/${props.libraryId}/audit-logs`,
      { params: { page: 1, page_size: 50 } },
    );
    logs.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    notifyError(getErrorMessage(error, "获取审计日志失败"));
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchLogs();
});
</script>

<template>
  <div class="flex flex-col gap-2">
    <div v-if="loading" class="text-sm text-muted-foreground">加载中...</div>
    <div v-else-if="logs.length === 0" class="text-sm text-muted-foreground">暂无审计日志</div>
    <div v-else class="flex flex-col gap-1">
      <div
        v-for="log in logs"
        :key="log.id"
        class="flex items-center gap-3 rounded border px-3 py-2 text-sm"
      >
        <span class="shrink-0 font-mono text-xs text-muted-foreground">
          {{ new Date(log.created_at).toLocaleString() }}
        </span>
        <span class="font-medium">{{ log.action }}</span>
        <span class="text-muted-foreground">{{ log.resource_type }}:{{ log.resource_id }}</span>
        <span v-if="log.detail" class="text-muted-foreground truncate">{{ log.detail }}</span>
      </div>
    </div>
  </div>
</template>
