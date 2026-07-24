<script setup lang="ts">
/**
 * 回收站标签页
 */

import { h, onMounted, ref } from "vue";
import { getRecycleItems, restoreRecycleItem, permanentDeleteRecycleItem, emptyRecycle } from "../../../api/recycle";
import { getErrorMessage, notifyError, notifySuccess, confirmAction } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import { Button, DataTable, useDataTable, Badge } from "@/components";
import type { RecycleItem } from "../../../types";
import type { ApiResponse } from "@/framework/api/types";
import type { ColumnDef } from "@tanstack/vue-table";
import { RotateCcw, Trash2 } from "@lucide/vue";

const props = defineProps<{
  libraryId: string;
}>();

const columns: ColumnDef<RecycleItem>[] = [
  { accessorKey: "resource_type", header: "资源类型", size: 120 },
  { accessorKey: "original_path", header: "原始路径", size: 300 },
  { accessorKey: "deleted_by", header: "删除人", size: 120 },
  {
    accessorKey: "status",
    header: "状态",
    size: 100,
    cell: ({ row }) =>
      h(Badge, { variant: row.original.status === "deleted" ? "destructive" : "secondary" }, () =>
        row.original.status,
      ),
  },
  {
    accessorKey: "created_at",
    header: "删除时间",
    size: 180,
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

const dataTable = useDataTable<RecycleItem>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getRecycleItems(props.libraryId, { page, page_size });
    return createPaginatedResponse<RecycleItem>(response);
  },
});

const handleRestore = async (itemId: string) => {
  try {
    await restoreRecycleItem(props.libraryId, itemId);
    notifySuccess("恢复成功");
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "恢复失败"));
  }
};

const handlePermanentDelete = async (itemId: string) => {
  if (!confirmAction("确定要永久删除吗？此操作不可撤销。")) return;
  try {
    await permanentDeleteRecycleItem(props.libraryId, itemId);
    notifySuccess("永久删除成功");
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "永久删除失败"));
  }
};

const handleEmptyRecycle = async () => {
  if (!confirmAction("确定要清空回收站吗？此操作不可撤销。")) return;
  try {
    await emptyRecycle(props.libraryId);
    notifySuccess("回收站已清空");
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "清空回收站失败"));
  }
};

onMounted(() => {
  dataTable.refresh();
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex justify-end">
      <Button variant="destructive" size="sm" @click="handleEmptyRecycle">
        <Trash2 class="mr-1 h-4 w-4" />
        清空回收站
      </Button>
    </div>
    <DataTable :data-table="dataTable" :fixed-layout="true" />
  </div>
</template>
