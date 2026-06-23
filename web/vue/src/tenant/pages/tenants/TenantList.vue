<script setup lang="ts">
import {
  Building2,
  Clock,
  Pencil,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  ShieldOff,
  Trash2,
  UserX,
} from "@lucide/vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { computed, h, ref } from "vue";
import { useRouter } from "vue-router";
import { Badge, Button, Card, DataTable, Input, useDataTable } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";
import { confirmAction } from "@/framework/utils/feedback";
import { getTenants } from "@/tenant/api/tenant";
import { useTenantStore } from "@/tenant/stores/tenant";
import type { Tenant, TenantListStats } from "@/tenant/types";

const router = useRouter();
const tenantStore = useTenantStore();
const adminAuthStore = useAdminAuthStore();

const searchForm = ref({
  keyword: "",
  status: "",
});

const stats = ref<TenantListStats>({
  total_count: 0,
  inactive_count: 0,
  expired_count: 0,
});

const statusOptions = [
  { label: "激活", value: "active" },
  { label: "停用", value: "inactive" },
];

const canCreate = computed(() => adminAuthStore.isLoggedIn);
const canEdit = computed(() => adminAuthStore.isLoggedIn);

function formatDate(dateStr?: string): string {
  if (!dateStr) return "永久";
  return new Date(dateStr).toLocaleDateString();
}

// 列定义
const tenantColumns: ColumnDef<Tenant>[] = [
  {
    accessorKey: "name",
    header: "租户信息",
    size: 200,
    cell: ({ row }) => {
      const tenant = row.original;
      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, tenant.name),
        h("div", { class: "text-muted-foreground text-xs" }, tenant.code),
      ]);
    },
  },
  {
    accessorKey: "contact_name",
    header: "联系人",
    size: 100,
    cell: ({ row }) => row.original.contact_name || "--",
  },
  {
    accessorKey: "contact_email",
    header: "联系人邮箱",
    size: 150,
    cell: ({ row }) => row.original.contact_email || "--",
  },
  {
    accessorKey: "status",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const status = row.original.status;
      return h(Badge, { variant: status === "active" ? "default" : "secondary" }, () =>
        status === "active" ? "激活" : "停用"
      );
    },
  },
  {
    accessorKey: "expired_at",
    header: "过期时间",
    size: 80,
    cell: ({ row }) => formatDate(row.original.expired_at),
  },
  {
    id: "actions",
    header: "操作",
    size: 200,
    cell: ({ row }) => {
      const tenant = row.original;
      const buttons = [
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleDetail(tenant) },
          () => "详情"
        ),
      ];

      if (canEdit.value) {
        buttons.push(
          h(Button, { variant: "ghost", size: "sm", onClick: () => handleEdit(tenant) }, () => [
            h(Pencil, { class: "mr-1 h-3.5 w-3.5" }),
            "编辑",
          ])
        );
      }

      if (canEdit.value && tenant.status === "inactive") {
        buttons.push(
          h(Button, { variant: "ghost", size: "sm", onClick: () => handleActivate(tenant) }, () => [
            h(ShieldCheck, { class: "mr-1 h-3.5 w-3.5" }),
            "激活",
          ])
        );
      }

      if (canEdit.value && tenant.status === "active") {
        buttons.push(
          h(
            Button,
            { variant: "ghost", size: "sm", onClick: () => handleDeactivate(tenant) },
            () => [h(ShieldOff, { class: "mr-1 h-3.5 w-3.5" }), "停用"]
          )
        );
      }

      if (canEdit.value) {
        buttons.push(
          h(
            Button,
            {
              variant: "ghost",
              size: "sm",
              class: "text-destructive hover:text-destructive",
              onClick: () => handleDelete(tenant),
            },
            () => [h(Trash2, { class: "mr-1 h-3.5 w-3.5" }), "删除"]
          )
        );
      }

      return h("div", { class: "flex items-center gap-1" }, buttons);
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<Tenant>({
  columns: tenantColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getTenants({
      page,
      page_size,
      keyword: searchForm.value.keyword || undefined,
      status: searchForm.value.status === "all" ? undefined : searchForm.value.status || undefined,
    });
    // 提取 stats 供统计卡片使用
    stats.value = response.stats ?? stats.value;
    return response;
  },
});

const handleSearch = () => {
  dataTable.refresh(true);
};

const handleReset = () => {
  searchForm.value = { keyword: "", status: "" };
  dataTable.refresh(true);
};

const handleCreate = () => {
  router.push("/admin/tenants/create");
};

const handleEdit = (row: Tenant) => {
  router.push(`/admin/tenants/${row.id}/edit`);
};

const handleDetail = (row: Tenant) => {
  router.push(`/admin/tenants/${row.id}`);
};

const handleDelete = async (row: Tenant) => {
  if (!(await confirmAction(`确定要删除租户 "${row.name}" 吗？删除后不可恢复。`))) return;

  try {
    await tenantStore.removeTenant(row.id);
    dataTable.refresh();
  } catch (error: unknown) {
    console.error("删除租户失败:", error);
    // Store 会处理错误通知
  }
};

const handleActivate = async (row: Tenant) => {
  try {
    await tenantStore.activate(row.id);
    dataTable.refresh();
  } catch (error: unknown) {
    console.error("激活租户失败:", error);
    // Store 会处理错误通知
  }
};

const handleDeactivate = async (row: Tenant) => {
  try {
    await tenantStore.deactivate(row.id);
    dataTable.refresh();
  } catch (error: unknown) {
    console.error("停用租户失败:", error);
    // Store 会处理错误通知
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold" data-testid="page-title">租户管理</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理系统租户，包括租户信息、资源配置和状态管理。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="dataTable.refresh()" data-testid="refresh-button">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button v-if="canCreate" @click="handleCreate" data-testid="create-tenant-button">
          <Plus class="mr-1 h-4 w-4" />
          新建租户
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <div class="border rounded-lg p-4 bg-card" data-testid="stats-total">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">租户总数</p>
            <p class="text-2xl font-bold mt-1" data-testid="stats-total-value">{{ stats.total_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">系统中的租户总数</p>
          </div>
          <Building2 class="h-8 w-8 opacity-20 text-blue-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card" data-testid="stats-inactive">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">未激活数</p>
            <p class="text-2xl font-bold mt-1" data-testid="stats-inactive-value">{{ stats.inactive_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">状态为停用的租户数量</p>
          </div>
          <UserX class="h-8 w-8 opacity-20 text-red-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card" data-testid="stats-expired">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">过期数</p>
            <p class="text-2xl font-bold mt-1" data-testid="stats-expired-value">{{ stats.expired_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">已过期的租户数量</p>
          </div>
          <Clock class="h-8 w-8 opacity-20 text-amber-500" />
        </div>
      </div>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <div class="border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">租户列表</div>
            <div class="text-muted-foreground mt-1 text-xs">管理系统租户及其资源配置</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Input
              v-model="searchForm.keyword"
              class="w-56"
              placeholder="租户名称或编码"
              data-testid="search-keyword"
              @keydown.enter="handleSearch"
            />
            <Select v-model="searchForm.status">
              <SelectTrigger class="w-[130px]" data-testid="search-status">
                <SelectValue placeholder="租户状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" @click="handleSearch" data-testid="search-button">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="outline" @click="handleReset" data-testid="reset-button">
              <RotateCcw class="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </div>
      </div>

      <div class="min-h-0 flex-1 overflow-hidden px-5 py-4">
        <DataTable :data-table="dataTable" :fixed-layout="true" data-testid="tenant-table" />
      </div>
    </Card>
  </div>
</template>
