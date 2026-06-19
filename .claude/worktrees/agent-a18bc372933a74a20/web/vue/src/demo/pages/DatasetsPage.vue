<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { storeToRefs } from "pinia";
import { useDatasetStore } from "@/demo/stores/datasets";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button, Input, Badge, Skeleton } from "@/components";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableEmpty,
} from "@/components/ui/table";

const datasetStore = useDatasetStore();
const { loading, error, datasets } = storeToRefs(datasetStore);

const searchQuery = ref("");

const filteredDatasets = computed(() => {
  if (!searchQuery.value) return datasets.value;
  const q = searchQuery.value.toLowerCase();
  return datasets.value.filter(
    (d) =>
      d.name.toLowerCase().includes(q) ||
      (d.description && d.description.toLowerCase().includes(q)),
  );
});

onMounted(() => {
  datasetStore.fetchDatasets();
});
</script>

<template>
  <AppPage title="知识库列表" variant="list">
    <template #actions>
      <Button>新建知识库</Button>
    </template>

    <div class="flex items-center gap-4">
      <Input v-model="searchQuery" placeholder="搜索知识库..." class="max-w-sm" />
    </div>

    <div v-if="loading" class="flex flex-col gap-2">
      <Skeleton class="h-10 w-full" />
      <Skeleton class="h-10 w-full" />
      <Skeleton class="h-10 w-full" />
    </div>

    <Table v-else-if="error">
      <TableEmpty :colspan="5" class="text-destructive">{{ error }}</TableEmpty>
    </Table>

    <Table v-else>
      <TableHeader>
        <TableRow>
          <TableHead>名称</TableHead>
          <TableHead>描述</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>创建时间</TableHead>
          <TableHead class="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableEmpty v-if="filteredDatasets.length === 0" :colspan="5">
          暂无知识库
        </TableEmpty>
        <TableRow v-for="item in filteredDatasets" :key="item.id">
          <TableCell class="font-medium">{{ item.name }}</TableCell>
          <TableCell class="text-muted-foreground">{{ item.description || "暂无描述" }}</TableCell>
          <TableCell>
            <Badge variant="success">活跃</Badge>
          </TableCell>
          <TableCell class="text-muted-foreground">{{ item.createdAt }}</TableCell>
          <TableCell class="text-right">
            <Button variant="outline" size="xs">查看</Button>
            <Button variant="ghost" size="xs" class="text-destructive">删除</Button>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </AppPage>
</template>