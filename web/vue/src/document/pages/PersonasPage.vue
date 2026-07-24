<script setup lang="ts">
/**
 * 人设管理页面
 */

import { h, onMounted, ref } from "vue";
import { confirmAction } from "@/framework/utils/feedback";
import { getPersonas, createPersona, updatePersona, deletePersona } from "../api/persona";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button, Input, DataTable, useDataTable, Dialog, DialogContent, Textarea } from "@/components";
import { DialogHeader, DialogTitle } from "@/components";
import { FormControl, FormField, FormItem, FormLabel } from "@/components";
import type { Persona } from "../types";
import type { ApiResponse } from "@/framework/api/types";
import type { ColumnDef } from "@tanstack/vue-table";
import { Plus, Search } from "@lucide/vue";

import { createPaginatedResponse } from "@/framework/api/types";
const keyword = ref("");
const createDialogOpen = ref(false);
const editDialogOpen = ref(false);
const saving = ref(false);
const editingPersona = ref<Persona | null>(null);
const formName = ref("");
const formInstruction = ref("");
const formDescription = ref("");

const columns: ColumnDef<Persona>[] = [
  { accessorKey: "name", header: "名称", size: 180 },
  {
    accessorKey: "instruction",
    header: "指令",
    size: 300,
    cell: ({ row }) => {
      const text = row.original.instruction;
      return h("span", { class: "truncate" }, text.length > 60 ? text.slice(0, 60) + "..." : text);
    },
  },
  { accessorKey: "description", header: "描述", size: 200 },
  {
    accessorKey: "created_at",
    header: "创建时间",
    size: 180,
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

const dataTable = useDataTable<Persona>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getPersonas({ page, page_size, keyword: keyword.value || undefined });
    return createPaginatedResponse<Persona>(response);
  },
});

const handleSearch = () => {
  dataTable.refresh();
};

const openCreate = () => {
  formName.value = "";
  formInstruction.value = "";
  formDescription.value = "";
  createDialogOpen.value = true;
};

const openEdit = (persona: Persona) => {
  editingPersona.value = persona;
  formName.value = persona.name;
  formInstruction.value = persona.instruction;
  formDescription.value = persona.description ?? "";
  editDialogOpen.value = true;
};

const handleCreate = async () => {
  saving.value = true;
  try {
    await createPersona({
      name: formName.value,
      instruction: formInstruction.value,
      description: formDescription.value || null,
    });
    notifySuccess("人设创建成功");
    createDialogOpen.value = false;
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "创建人设失败"));
  } finally {
    saving.value = false;
  }
};

const handleUpdate = async () => {
  if (!editingPersona.value) return;
  saving.value = true;
  try {
    await updatePersona(editingPersona.value.id, {
      name: formName.value,
      instruction: formInstruction.value,
      description: formDescription.value || null,
    });
    notifySuccess("人设更新成功");
    editDialogOpen.value = false;
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "更新人设失败"));
  } finally {
    saving.value = false;
  }
};

const handleDelete = async (id: string) => {
  if (!confirmAction("确定要删除该人设吗？")) return;
  try {
    await deletePersona(id);
    notifySuccess("人设删除成功");
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "删除人设失败"));
  }
};

onMounted(() => {
  dataTable.refresh();
});
</script>

<template>
  <AppPage title="人设管理">
    <template #actions>
      <Button @click="openCreate">
        <Plus class="mr-1 h-4 w-4" />
        新建人设
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
                placeholder="搜索人设名称"
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
      <DialogContent class="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle>新建人设</DialogTitle>
        </DialogHeader>
        <form class="flex flex-col gap-4" @submit.prevent="handleCreate">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem>
              <FormLabel>名称</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="formName" placeholder="输入人设名称" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="instruction">
            <FormItem>
              <FormLabel>指令</FormLabel>
              <FormControl>
                <Textarea
                  v-bind="componentField"
                  v-model="formInstruction"
                  placeholder="输入人设指令内容"
                  :rows="6"
                  class="font-mono text-sm"
                />
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
      <DialogContent class="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle>编辑人设</DialogTitle>
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
          <FormField v-slot="{ componentField }" name="instruction">
            <FormItem>
              <FormLabel>指令</FormLabel>
              <FormControl>
                <Textarea
                  v-bind="componentField"
                  v-model="formInstruction"
                  :rows="6"
                  class="font-mono text-sm"
                />
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
