<script setup lang="ts">
/**
 * 文档库列表页面
 */

import { h, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button, Input, DataTable, useDataTable, Badge, Dialog, DialogContent } from "@/components";
import {
  DialogHeader,
  DialogTitle,
} from "@/components";
import { FormControl, FormField, FormItem, FormLabel } from "@/components";
import type { ColumnDef } from "@tanstack/vue-table";
import type { Library } from "../../types";
import type { ApiResponse } from "@/framework/api/types";
import { getLibraries, createLibrary } from "../../api/library";
import { Plus, Search } from "@lucide/vue";

const router = useRouter();
const keyword = ref("");
const createDialogOpen = ref(false);
const creating = ref(false);
const newLibraryName = ref("");
const newLibraryCode = ref("");
const newLibraryDescription = ref("");

const columns: ColumnDef<Library>[] = [
  { accessorKey: "name", header: "名称", size: 200 },
  { accessorKey: "code", header: "编码", size: 120 },
  { accessorKey: "type", header: "类型", size: 100 },
  {
    accessorKey: "enabled",
    header: "状态",
    size: 80,
    cell: ({ row }) =>
      h(Badge, { variant: row.original.enabled ? "default" : "secondary" }, () =>
        row.original.enabled ? "启用" : "停用",
      ),
  },
  {
    accessorKey: "created_at",
    header: "创建时间",
    size: 180,
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

const dataTable = useDataTable<Library>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getLibraries({ page, page_size, keyword: keyword.value || undefined });
    return createPaginatedResponse<Library>(response);
  },
});

const handleSearch = () => {
  dataTable.refresh();
};

const handleCreate = async () => {
  creating.value = true;
  try {
    const library = await createLibrary({
      name: newLibraryName.value,
      code: newLibraryCode.value,
      description: newLibraryDescription.value || null,
      type: "knowledge_base",
    });
    notifySuccess("文档库创建成功");
    createDialogOpen.value = false;
    newLibraryName.value = "";
    newLibraryCode.value = "";
    newLibraryDescription.value = "";
    dataTable.refresh();
    if (library?.id) {
      router.push(`/document/libraries/${library.id}`);
    }
  } catch (error) {
    notifyError(getErrorMessage(error, "创建文档库失败"));
  } finally {
    creating.value = false;
  }
};

const handleRowClick = (row: Library) => {
  router.push(`/document/libraries/${row.id}`);
};

onMounted(() => {
  dataTable.refresh();
});
</script>

<template>
  <AppPage title="文档库">
    <template #actions>
      <Button @click="createDialogOpen = true">
        <Plus class="mr-1 h-4 w-4" />
        新建文档库
      </Button>
    </template>

    <div class="flex h-full min-h-0 flex-col gap-4 p-4">
      <div class="ring-foreground/10 bg-card rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
        <!-- 搜索区域 -->
        <div class="shrink-0 border-b px-5 py-4">
          <div class="flex items-end gap-3">
            <div class="flex flex-col gap-1">
              <span class="text-xs text-muted-foreground">关键词</span>
              <Input
                v-model="keyword"
                placeholder="搜索文档库名称/编码"
                class="w-[240px]"
                @keyup.enter="handleSearch"
              />
            </div>
            <Button size="sm" @click="handleSearch">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
          </div>
        </div>

        <!-- 数据表格区域 -->
        <div class="flex min-h-0 flex-1 flex-col p-3">
          <DataTable :data-table="dataTable" :fixed-layout="true" @row-click="handleRowClick" />
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <Dialog v-model:open="createDialogOpen">
      <DialogContent class="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>新建文档库</DialogTitle>
        </DialogHeader>
        <form class="flex flex-col gap-4" @submit.prevent="handleCreate">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem>
              <FormLabel>名称</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="newLibraryName" placeholder="输入文档库名称" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="code">
            <FormItem>
              <FormLabel>编码</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="newLibraryCode" placeholder="输入文档库编码" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="description">
            <FormItem>
              <FormLabel>描述</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="newLibraryDescription" placeholder="输入描述（可选）" />
              </FormControl>
            </FormItem>
          </FormField>
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="createDialogOpen = false">取消</Button>
            <Button type="submit" :disabled="creating || !newLibraryName || !newLibraryCode">
              {{ creating ? "创建中..." : "创建" }}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
