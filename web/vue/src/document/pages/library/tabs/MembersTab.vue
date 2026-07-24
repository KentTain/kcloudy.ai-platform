<script setup lang="ts">
/**
 * 成员管理标签页
 */

import { h, onMounted, ref } from "vue";
import { getMembers, createMember, deleteMember } from "../../../api/member";
import { getErrorMessage, notifyError, notifySuccess, confirmAction } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import { Button, Input, DataTable, useDataTable, Badge, Dialog, DialogContent } from "@/components";
import { DialogHeader, DialogTitle } from "@/components";
import { FormControl, FormField, FormItem, FormLabel } from "@/components";
import type { LibraryMember } from "../../../types";
import type { ApiResponse } from "@/framework/api/types";
import type { ColumnDef } from "@tanstack/vue-table";
import { Plus, Trash2 } from "@lucide/vue";

const props = defineProps<{
  libraryId: string;
}>();

const createDialogOpen = ref(false);
const creating = ref(false);
const newUserId = ref("");
const newUserName = ref("");
const newRole = ref("viewer");

const columns: ColumnDef<LibraryMember>[] = [
  { accessorKey: "user_name", header: "用户名", size: 180 },
  { accessorKey: "role", header: "角色", size: 120 },
  {
    accessorKey: "status",
    header: "状态",
    size: 100,
    cell: ({ row }) =>
      h(Badge, { variant: row.original.status === "active" ? "default" : "secondary" }, () =>
        row.original.status,
      ),
  },
  { accessorKey: "remarks", header: "备注", size: 200 },
  {
    accessorKey: "created_at",
    header: "加入时间",
    size: 180,
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

const dataTable = useDataTable<LibraryMember>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getMembers(props.libraryId, { page, page_size });
    return createPaginatedResponse<LibraryMember>(response);
  },
});

const handleCreate = async () => {
  creating.value = true;
  try {
    await createMember(props.libraryId, {
      user_id: newUserId.value,
      user_name: newUserName.value,
      role: newRole.value,
    } as Partial<LibraryMember>);
    notifySuccess("成员添加成功");
    createDialogOpen.value = false;
    newUserId.value = "";
    newUserName.value = "";
    newRole.value = "viewer";
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "添加成员失败"));
  } finally {
    creating.value = false;
  }
};

const handleDelete = async (memberId: string) => {
  if (!confirmAction("确定要移除该成员吗？")) return;
  try {
    await deleteMember(props.libraryId, memberId);
    notifySuccess("成员移除成功");
    dataTable.refresh();
  } catch (error) {
    notifyError(getErrorMessage(error, "移除成员失败"));
  }
};

onMounted(() => {
  dataTable.refresh();
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex justify-end">
      <Button @click="createDialogOpen = true">
        <Plus class="mr-1 h-4 w-4" />
        添加成员
      </Button>
    </div>
    <DataTable :data-table="dataTable" :fixed-layout="true" />

    <!-- 添加成员弹窗 -->
    <Dialog v-model:open="createDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>添加成员</DialogTitle>
        </DialogHeader>
        <form class="flex flex-col gap-4" @submit.prevent="handleCreate">
          <FormField v-slot="{ componentField }" name="user_id">
            <FormItem>
              <FormLabel>用户ID</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="newUserId" placeholder="输入用户ID" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="user_name">
            <FormItem>
              <FormLabel>用户名</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="newUserName" placeholder="输入用户名" />
              </FormControl>
            </FormItem>
          </FormField>
          <FormField v-slot="{ componentField }" name="role">
            <FormItem>
              <FormLabel>角色</FormLabel>
              <FormControl>
                <Input v-bind="componentField" v-model="newRole" placeholder="viewer / editor / admin" />
              </FormControl>
            </FormItem>
          </FormField>
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="createDialogOpen = false">取消</Button>
            <Button type="submit" :disabled="creating || !newUserName">
              {{ creating ? "添加中..." : "添加" }}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
