<script setup lang="ts">
/**
 * 标签管理页面
 */

import { h, onMounted, ref } from "vue";
import { confirmAction } from "@/framework/utils/feedback";
import { getTags, createTag, updateTag, deleteTag } from "../api/tag";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button, Input, DataTable, useDataTable, Badge, Dialog, DialogContent } from "@/components";
import { DialogHeader, DialogTitle } from "@/components";
import { FormControl, FormField, FormItem, FormLabel } from "@/components";
import type { Tag } from "../types";
import type { ApiResponse } from "@/framework/api/types";
import type { ColumnDef } from "@tanstack/vue-table";
import { Plus, Search } from "@lucide/vue";

import { createPaginatedResponse } from "@/framework/api/types";
const keyword = ref("");
const createDialogOpen = ref(false);
const editDialogOpen = ref(false);
const saving = ref(false);
const editingTag = ref<Tag | null>(null);
const formName = ref("");
const formDescription = ref("");

const columns: ColumnDef<Tag>[] = [
  { accessorKey: "name", header: "名称", size: 200 },
  { accessorKey: "description", header: "描述", size: 250 },
  {
    accessorKey: "color",
    header: "颜色",
    size: 80,
    cell: ({ row }) =>
      row.original.color
        ? h("div", {
            class: "h-4 w-4 rounded-full",
            style: { backgroundColor: row.original.color },
          })
        : "-",
  },
  { accessorKey: "doc_count", header: "文档数", size: 100 },
  {
    accessorKey: "created_at",
    header: "创建时间",
    size: 180,
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

const dataTable = useDataTable<Tag>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getTags({ page, page_size, keyword: keyword.value || undefined });
    return createPaginatedResponse<Tag>(response);
  },
});

const handleSearch = () => {
  dataTable.refresh();
};

const openCreate = () => {
  formName.value = "";
  formDescription.value = "";
  createDialogOpen.value = true;
};

const openEdit = (tag: Tag) => {
  editingTag.value = tag;
  formName.value = tag.name;
  formDescription.value = tag.description ?? "";
  editDialogOpen.value = true;
};

const handleCreate = async () => {
  saving.value = true;
  try {
    await createTag({ name: formName.value, description: formDescription.value || null });
    notifySuccess("标签创建成功");
    createDialogOpen.value = false;
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "创建标签失败"));
  } finally {
    saving.value = false;
  }
};

const handleUpdate = async () => {
  if (!editingTag.value) return;
  saving.value = true;
  try {
    await updateTag(editingTag.value.id, {
      name: formName.value,
      description: formDescription.value || null,
    });
    notifySuccess("标签更新成功");
    editDialogOpen.value = false;
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "更新标签失败"));
  } finally {
    saving.value = false;
  }
};

const handleDelete = async (id: string) => {
  if (!confirmAction("确定要删除该标签吗？")) return;
  try {
    await deleteTag(id);
    notifySuccess("标签删除成功");
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "删除标签失败"));
  }
};

onMounted(() => {
  dataTable.refresh();
});
</script>

<template>
  <AppPage title="标签管理">
    <template #actions>
      <Button @click="openCreate">
        <Plus class="mr-1 h-4 w-4" />
        新建标签
      </Button>
    </template>

    <div class="flex h-full min-h-0 flex-col gap-4 p-4">
      <div class="ring-foreground/10 bg-card rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
        <div class="shrink-0 border-b px-5 py-4">
          <div class="flex items-end gap-3">
            <div class="flex flex-col gap-1">
              <span class="text-xs text-muted-foreground">关键词</span>
              <Input
                v-model="keyword"
                placeholder="搜索标签名称"
                class="w-[200px]"
                @keyup.enter="handleSearch"
              />
            </div>
            <Button size="sm" @click="handleSearch">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
          </div>
        </div>
        <div class="flex min-h-0 flex-1 flex-col p-3">
          <DataTable :data-table="dataTable" :fixed-layout="true" />
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <Dialog v-model:open="createDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>新建标签</DialogTitle>
        </DialogHeader>
        <form class="flex flex-col gap-4" @submit.prevent="handleCreate">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem>
              <FormLabel>名称</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="formName" placeholder="输入标签名称" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="description">
            <FormItem>
              <FormLabel>描述</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="formDescription" placeholder="输入描述（可选）" />
              </FormControl>
            </FormItem>
          </FormField>
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="createDialogOpen = false">取消</Button>
            <Button type="submit" :disabled="saving || !formName">{{ saving ? "创建中..." : "创建" }}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>

    <!-- 编辑弹窗 -->
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>编辑标签</DialogTitle>
        </DialogHeader>
        <form class="flex flex-col gap-4" @submit.prevent="handleUpdate">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem>
              <FormLabel>名称</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="formName" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="description">
            <FormItem>
              <FormLabel>描述</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="formDescription" />
              </FormControl>
            </FormItem>
          </FormField>
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="editDialogOpen = false">取消</Button>
            <Button type="submit" :disabled="saving || !formName">{{ saving ? "保存中..." : "保存" }}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
