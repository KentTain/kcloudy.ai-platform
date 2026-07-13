<script setup lang="ts">
/**
 * 插件安装记录列表页面
 *
 * 展示所有租户的插件安装记录，仅提供卸载功能。
 * 状态为 ACTIVE 时禁止卸载，需先停止插件。
 */
import { h, ref } from "vue";
import {
  Eye,
  Package,
  RefreshCw,
  RotateCcw,
  Search,
  Users,
} from "@lucide/vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { Badge, Button, Card, DataTable, Input, useDataTable } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { confirmAction, notifyError, notifySuccess } from "@/framework/utils/feedback";
import {
  getPluginInstallations,
  uninstallPluginInstallation,
} from "@/tenant/api/plugin";
import type { PluginInstallation, PluginInstallationQuery } from "@/tenant/api/plugin";
import { PluginInstallationRowActions } from "@/tenant/components";

// 搜索筛选
const searchForm = ref<PluginInstallationQuery>({
  tenant_id: "",
  plugin_id: "",
  status: "",
});

// 统计数据
const stats = ref({
  total: 0,
  active: 0,
  inactive: 0,
});

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 状态颜色映射
const statusColorMap: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  ACTIVE: "default",
  INACTIVE: "outline",
  PENDING: "outline",
  FAILED: "destructive",
};

// 状态文本映射
const statusTextMap: Record<string, string> = {
  ACTIVE: "运行中",
  INACTIVE: "已停止",
  PENDING: "待安装",
  FAILED: "安装失败",
};

// 卸载中的记录集合
const uninstallingKeys = ref<Set<string>>(new Set());

// 列定义
const columns: ColumnDef<PluginInstallation>[] = [
  {
    accessorKey: "plugin_id",
    header: "插件信息",
    size: 280,
    cell: ({ row }) => {
      const installation = row.original;
      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, installation.plugin_id),
        h(
          "div",
          { class: "text-muted-foreground text-xs font-mono" },
          installation.plugin_unique_identifier
        ),
      ]);
    },
  },
  {
    accessorKey: "tenant_id",
    header: "租户 ID",
    size: 150,
    cell: ({ row }) =>
      h("div", { class: "font-mono text-sm" }, row.original.tenant_id),
  },
  {
    accessorKey: "plugin_type",
    header: "类型",
    size: 80,
    cell: ({ row }) => {
      const type = row.original.plugin_type || "unknown";
      return h(Badge, { variant: "outline" }, () => type);
    },
  },
  {
    accessorKey: "status",
    header: "状态",
    size: 100,
    cell: ({ row }) => {
      const status = row.original.status;
      return h(
        Badge,
        { variant: statusColorMap[status] || "outline" },
        () => statusTextMap[status] || status
      );
    },
  },
  {
    accessorKey: "installed_at",
    header: "安装时间",
    size: 150,
    cell: ({ row }) => formatDate(row.original.installed_at),
  },
  {
    id: "actions",
    header: "操作",
    size: 100,
    cell: ({ row }) => {
      const installation = row.original;
      const key = `${installation.tenant_id}:${installation.plugin_id}`;
      const isUninstalling = uninstallingKeys.value.has(key);
      return h(PluginInstallationRowActions, {
        row: installation,
        isUninstalling,
        onUninstall: handleUninstall,
      });
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<PluginInstallation>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getPluginInstallations({
      page,
      page_size,
      tenant_id: searchForm.value.tenant_id || undefined,
      plugin_id: searchForm.value.plugin_id || undefined,
      status: searchForm.value.status || undefined,
    });

    if (response.code === 200) {
      const items = response.data || [];
      stats.value = {
        total: response.total || 0,
        active: items.filter((i) => i.status === "ACTIVE").length,
        inactive: items.filter((i) => i.status === "INACTIVE").length,
      };
    }

    return response;
  },
});

// 搜索
const handleSearch = () => {
  dataTable.refresh(true);
};

// 重置
const handleReset = () => {
  searchForm.value = { tenant_id: "", plugin_id: "", status: "" };
  dataTable.refresh(true);
};

// 卸载插件
const handleUninstall = async (installation: PluginInstallation) => {
  if (installation.status === "ACTIVE") {
    notifyError("运行中的插件禁止卸载，请先停止插件");
    return;
  }

  if (
    !(await confirmAction(
      `确定卸载插件 "${installation.plugin_id}"（租户: ${installation.tenant_id}）吗？卸载后不可恢复。`
    ))
  )
    return;

  const key = `${installation.tenant_id}:${installation.plugin_id}`;
  uninstallingKeys.value.add(key);

  try {
    await uninstallPluginInstallation(
      installation.tenant_id,
      installation.plugin_id
    );
    notifySuccess("插件已卸载");
    dataTable.refresh();
  } catch (error: any) {
    console.error("卸载插件失败:", error);
    const errorMessage =
      error?.response?.data?.msg || error?.message || "卸载失败";
    notifyError(errorMessage);
  } finally {
    uninstallingKeys.value.delete(key);
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-installation-list-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold">插件安装记录</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理各租户的插件安装记录，仅支持卸载操作。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" data-testid="refresh-btn" @click="dataTable.refresh()">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <Card class="p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">安装总数</p>
            <p class="text-2xl font-bold mt-1">{{ stats.total }}</p>
            <p class="text-xs text-muted-foreground mt-1">所有租户的插件安装总数</p>
          </div>
          <Package class="h-8 w-8 opacity-20 text-blue-500" />
        </div>
      </Card>
      <Card class="p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">运行中</p>
            <p class="text-2xl font-bold mt-1">{{ stats.active }}</p>
            <p class="text-xs text-muted-foreground mt-1">状态为 ACTIVE 的安装数</p>
          </div>
          <Users class="h-8 w-8 opacity-20 text-green-500" />
        </div>
      </Card>
      <Card class="p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">已停止</p>
            <p class="text-2xl font-bold mt-1">{{ stats.inactive }}</p>
            <p class="text-xs text-muted-foreground mt-1">状态为 INACTIVE 的安装数</p>
          </div>
          <Eye class="h-8 w-8 opacity-20 text-amber-500" />
        </div>
      </Card>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <div class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">安装记录列表</div>
            <div class="text-muted-foreground mt-1 text-xs">管理租户插件安装记录</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Input
              v-model="searchForm.tenant_id"
              class="w-40"
              placeholder="租户 ID"
              data-testid="search-tenant-input"
              @keydown.enter="handleSearch"
            />
            <Input
              v-model="searchForm.plugin_id"
              class="w-40"
              placeholder="插件 ID"
              data-testid="search-plugin-input"
              @keydown.enter="handleSearch"
            />
            <Select v-model="searchForm.status">
              <SelectTrigger class="w-[120px]" data-testid="status-select">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="ACTIVE">运行中</SelectItem>
                <SelectItem value="INACTIVE">已停止</SelectItem>
                <SelectItem value="PENDING">待安装</SelectItem>
                <SelectItem value="FAILED">安装失败</SelectItem>
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

      <div class="flex min-h-0 flex-1 flex-col px-5 pt-4">
        <DataTable
          data-testid="plugin-installation-table"
          :data-table="dataTable"
          :fixed-layout="true"
        />
      </div>
    </div>
  </div>
</template>
