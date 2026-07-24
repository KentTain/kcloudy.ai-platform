<script setup lang="ts">
/**
 * 文档库详情页面
 */

import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useLibraryStore } from "../../stores/library";
import { getErrorMessage, notifyError, notifySuccess, confirmAction } from "@/framework/utils/feedback";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button, Badge, DescriptionList, type DescriptionItem } from "@/components";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components";
import FilesTab from "./tabs/FilesTab.vue";
import MembersTab from "./tabs/MembersTab.vue";
import PermissionTab from "./tabs/PermissionTab.vue";
import RecycleTab from "./tabs/RecycleTab.vue";
import { Trash2 } from "@lucide/vue";
import { deleteLibrary } from "../../api/library";

const route = useRoute();
const router = useRouter();
const store = useLibraryStore();
const activeTab = ref("files");

const libraryId = computed(() => route.params.id as string);

const loadDetail = async () => {
  try {
    await store.fetchLibrary(libraryId.value);
  } catch (error) {
    notifyError(getErrorMessage(error, "加载文档库详情失败"));
  }
};

const descriptionItems = computed<DescriptionItem[]>(() => {
  const lib = store.currentLibrary;
  if (!lib) return [];
  return [
    { label: "名称", value: lib.name },
    { label: "编码", value: lib.code },
    { label: "类型", value: lib.type },
    {
      label: "状态",
      value: lib.enabled ? "启用" : "停用",
      type: "badge",
      badgeVariant: lib.enabled ? "default" : "secondary",
    },
    { label: "允许提交知识库", value: lib.allow_submit_to_kb ? "是" : "否" },
    { label: "描述", value: lib.description ?? "-" },
    { label: "创建时间", value: new Date(lib.created_at).toLocaleString() },
  ];
});

const handleDelete = async () => {
  if (!confirmAction("确定要删除该文档库吗？此操作不可撤销。")) return;
  try {
    await deleteLibrary(libraryId.value);
    notifySuccess("文档库删除成功");
    router.push("/document/libraries");
  } catch (error) {
    notifyError(getErrorMessage(error, "删除文档库失败"));
  }
};

onMounted(() => {
  loadDetail();
});
</script>

<template>
  <AppPage :title="store.currentLibrary?.name ?? '文档库详情'" variant="detail">
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="router.back()">返回</Button>
        <Button variant="outline" @click="handleDelete">
          <Trash2 class="mr-1 h-4 w-4" />
          删除
        </Button>
      </div>
    </template>

    <!-- 基本信息 -->
    <DescriptionList :items="descriptionItems" :columns="2" bordered />

    <!-- 标签页 -->
    <Tabs v-model="activeTab" class="mt-4">
      <TabsList>
        <TabsTrigger value="files">文件</TabsTrigger>
        <TabsTrigger value="members">成员</TabsTrigger>
        <TabsTrigger value="permission">权限</TabsTrigger>
        <TabsTrigger value="recycle">回收站</TabsTrigger>
      </TabsList>
      <TabsContent value="files">
        <FilesTab :library-id="libraryId" />
      </TabsContent>
      <TabsContent value="members">
        <MembersTab :library-id="libraryId" />
      </TabsContent>
      <TabsContent value="permission">
        <PermissionTab :library-id="libraryId" />
      </TabsContent>
      <TabsContent value="recycle">
        <RecycleTab :library-id="libraryId" />
      </TabsContent>
    </Tabs>
  </AppPage>
</template>
