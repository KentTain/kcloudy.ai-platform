<script setup lang="ts">
import {
  Eye,
  Package,
  Pencil,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Trash2,
  CheckCircle,
  Star,
  Users,
} from "@lucide/vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { h, ref } from "vue";
import { useRouter } from "vue-router";
import { Badge, Button, Card, DataTable, Input, useDataTable } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { confirmAction, notifyError, notifySuccess } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import { deleteModule, getModules } from "@/tenant/api/module";
import type { Module } from "@/tenant/types/admin";

const router = useRouter();

// 搜索筛选
const searchForm = ref({
  keyword: "",
  is_active: "",
});

// 统计数据
const stats = ref({
  totalCount: 0,
  activeCount: 0,
  needCount: 0,
  assignedCount: 0,
});

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 列定义
const moduleColumns: ColumnDef<Module>[] = [
  {
    accessorKey: "name",
    header: "模块信息",
    size: 200,
    cell: ({ row }) => {
      const module = row.original;
      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, module.name),
        h("div", { class: "text-muted-foreground text-xs" }, module.code),
      ]);
    },
  },
  {
    accessorKey: "is_active",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const isActive = row.original.is_active;
      return h(
        Badge,
        { variant: isActive ? "default" : "secondary" },
        () => (isActive ? "启用" : "停用")
      );
    },
  },
  {
    accessorKey: "is_need",
    header: "必须模块",
    size: 100,
    cell: ({ row }) => {
      const isNeed = row.original.is_need;
      return h(Badge, { variant: isNeed ? "default" : "outline" }, () => (isNeed ? "是" : "否"));
    },
  },
  {
    accessorKey: "tenant_count",
    header: "分配次数",
    size: 100,
    cell: ({ row }) => row.original.tenant_count || 0,
  },
  {
    accessorKey: "created_at",
    header: "创建时间",
    size: 120,
    cell: ({ row }) => formatDate(row.original.created_at),
  },
  {
    id: "actions",
    header: "操作",
    size: 160,
    cell: ({ row }) => {
      const module = row.original;
      return h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleDetail(module) },
          () => [h(Eye, { class: "mr-1 h-3.5 w-3.5" }), "详情"]
        ),
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleEdit(module) },
          () => [h(Pencil, { class: "mr-1 h-3.5 w-3.5" }), "编辑"]
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            class: "text-destructive hover:text-destructive",
            onClick: () => handleDelete(module),
          },
          () => [h(Trash2, { class: "mr-1 h-3.5 w-3.5" }), "删除"]
        ),
      ]);
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<Module>({
  columns: moduleColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getModules({
      page,
      page_size,
      keyword: searchForm.value.keyword || undefined,
      is_active:
        searchForm.value.is_active === "" || searchForm.value.is_active === "all"
          ? undefined
          : searchForm.value.is_active === "true",
    });
    // 提取统计数据
    const items = response.data;
    if (items) {
      stats.value = {
        totalCount: response.total || 0,
        activeCount: items.filter((item) => item.is_active).length,
        needCount: items.filter((item) => item.is_need).length,
        assignedCount: items.reduce((sum, item) => sum + (item.tenant_count || 0), 0),
      };
    }
    return createPaginatedResponse(response);
  },
});

// 搜索
const handleSearch = () => {
  dataTable.refresh(true);
};

// 重置
const handleReset = () => {
  searchForm.value = { keyword: "", is_active: "" };
  dataTable.refresh(true);
};

// 新增模块
const handleCreate = () => {
  router.push("/admin/modules/create");
};

// 查看详情
const handleDetail = (row: Module) => {
  router.push(`/admin/modules/${row.id}`);
};

// 编辑模块
const handleEdit = (row: Module) => {
  router.push(`/admin/modules/${row.id}/edit`);
};

// 删除模块
const handleDelete = async (row: Module) => {
  if (!(await confirmAction(`确定要删除模块 "${row.name}" 吗？删除后不可恢复。`))) return;

  try {
    await deleteModule(row.id);
    notifySuccess("模块已删除");
    dataTable.refresh();
  } catch (error: any) {
    console.error("删除模块失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "删除失败";
    notifyError(errorMessage);
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="module-list-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold">模块管理</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理系统模块，包括模块信息、菜单、权限和角色配置。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" data-testid="refresh-btn" @click="dataTable.refresh()">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button data-testid="create-module-btn" @click="handleCreate">
          <Plus class="mr-1 h-4 w-4" />
          新增模块
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">模块总数</p>
            <p class="text-2xl font-bold mt-1">{{ stats.totalCount }}</p>
            <p class="text-xs text-muted-foreground mt-1">已配置的系统模块数量</p>
          </div>
          <Package class="h-8 w-8 opacity-20 text-blue-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">启用模块</p>
            <p class="text-2xl font-bold mt-1">{{ stats.activeCount }}</p>
            <p class="text-xs text-muted-foreground mt-1">当前启用状态的模块数量</p>
          </div>
          <CheckCircle class="h-8 w-8 opacity-20 text-green-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">必须模块</p>
            <p class="text-2xl font-bold mt-1">{{ stats.needCount }}</p>
            <p class="text-xs text-muted-foreground mt-1">租户必须分配的模块数量</p>
          </div>
          <Star class="h-8 w-8 opacity-20 text-amber-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">已分配次数</p>
            <p class="text-2xl font-bold mt-1">{{ stats.assignedCount }}</p>
            <p class="text-xs text-muted-foreground mt-1">所有模块分配给租户的总次数</p>
          </div>
          <Users class="h-8 w-8 opacity-20 text-indigo-500" />
        </div>
      </div>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <div class="border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">模块列表</div>
            <div class="text-muted-foreground mt-1 text-xs">管理系统模块及其菜单、权限、角色配置</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Input
              v-model="searchForm.keyword"
              class="w-56"
              placeholder="搜索模块名称或编码"
              data-testid="search-keyword-input"
              @keydown.enter="handleSearch"
            />
            <Select v-model="searchForm.is_active">
              <SelectTrigger class="w-[130px]" data-testid="status-select">
                <SelectValue placeholder="模块状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="true">启用</SelectItem>
                <SelectItem value="false">停用</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" data-testid="search-btn" @click="handleSearch">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="outline" data-testid="reset-btn" @click="handleReset">
              <RotateCcw class="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </div>
      </div>

      <div class="min-h-0 flex-1 overflow-hidden px-5 py-4">
        <DataTable data-testid="module-table" :data-table="dataTable" :fixed-layout="true" />
      </div>
    </Card>
  </div>
</template>
