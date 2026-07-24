<script setup lang="ts">
/**
 * 文件管理标签页
 */

import { h, onMounted, ref, watch } from "vue";
import { getDocuments } from "../../../api/document";
import { getFolders } from "../../../api/folder";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import { Button, Input, DataTable, useDataTable, Badge } from "@/components";
import FolderTree from "../../../components/FolderTree.vue";
import type { Document, Folder } from "../../../types";
import type { ApiResponse } from "@/framework/api/types";
import type { ColumnDef } from "@tanstack/vue-table";
import { Search } from "@lucide/vue";

const props = defineProps<{
  libraryId: string;
}>();

const keyword = ref("");
const currentFolderId = ref<string | null>(null);
const folders = ref<Folder[]>([]);

const columns: ColumnDef<Document>[] = [
  { accessorKey: "name", header: "名称", size: 250 },
  { accessorKey: "document_type", header: "类型", size: 100 },
  {
    accessorKey: "lifecycle_status",
    header: "状态",
    size: 100,
    cell: ({ row }) =>
      h(Badge, { variant: row.original.lifecycle_status === "active" ? "default" : "secondary" }, () =>
        row.original.lifecycle_status,
      ),
  },
  {
    accessorKey: "file_size",
    header: "大小",
    size: 100,
    cell: ({ row }) => `${(row.original.file_size / 1024).toFixed(1)} KB`,
  },
  {
    accessorKey: "processing_status",
    header: "处理状态",
    size: 120,
    cell: ({ row }) =>
      h(Badge, { variant: row.original.processing_status === "completed" ? "default" : "outline" }, () =>
        row.original.processing_status,
      ),
  },
  {
    accessorKey: "created_at",
    header: "创建时间",
    size: 180,
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

const dataTable = useDataTable<Document>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getDocuments({
      page,
      page_size,
      library_id: props.libraryId,
      folder_id: currentFolderId.value ?? undefined,
      keyword: keyword.value || undefined,
    });
    return createPaginatedResponse<Document>(response);
  },
});

const fetchFolders = async () => {
  try {
    const response = await getFolders({ library_id: props.libraryId, page: 1, page_size: 500 });
    folders.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    notifyError(getErrorMessage(error, "获取文件夹列表失败"));
  }
};

const handleSearch = () => {
  dataTable.refresh();
};

onMounted(() => {
  fetchFolders();
  dataTable.refresh();
});

watch(currentFolderId, () => {
  dataTable.refresh();
});
</script>

<template>
  <div class="flex gap-4">
    <!-- 文件夹树侧栏 -->
    <div class="w-[220px] shrink-0 rounded-lg border p-3">
      <h4 class="mb-2 text-sm font-medium">文件夹</h4>
      <FolderTree v-model="currentFolderId" :library-id="libraryId" />
    </div>

    <!-- 文件列表 -->
    <div class="min-h-0 flex-1">
      <div class="mb-3 flex items-end gap-3">
        <div class="flex flex-col gap-1">
          <span class="text-xs text-muted-foreground">搜索</span>
          <Input
            v-model="keyword"
            placeholder="搜索文件名"
            class="w-[200px]"
            @keyup.enter="handleSearch"
          />
        </div>
        <Button size="sm" @click="handleSearch">
          <Search class="mr-1 h-4 w-4" />
          搜索
        </Button>
      </div>
      <DataTable :data-table="dataTable" :fixed-layout="true" />
    </div>
  </div>
</template>
