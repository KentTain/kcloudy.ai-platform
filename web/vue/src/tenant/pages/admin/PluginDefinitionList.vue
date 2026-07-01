<script setup lang="ts">
import {
  Eye,
  Package,
  Pencil,
  RefreshCw,
  RotateCcw,
  Search,
  Trash2,
  CheckCircle,
  Star,
  Users,
  Upload,
  FolderSearch,
  Download,
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { confirmAction, notifyError, notifySuccess } from "@/framework/utils/feedback";
import {
  deletePluginDefinition,
  getPluginDefinitions,
  getPluginStatistics,
  updatePluginDefinition,
} from "@/tenant/api/plugin";
import type { PluginDefinition, PluginStatistics } from "@/tenant/api/plugin";
import InstallToTenantsDialog from "./InstallToTenantsDialog.vue";

const router = useRouter();

const installDialogOpen = ref(false);
const installTargetPlugin = ref<PluginDefinition | null>(null);

const handleInstallToTenants = (row: PluginDefinition) => {
  installTargetPlugin.value = row;
  installDialogOpen.value = true;
};

const handleInstalled = () => {
  dataTable.refresh();
  loadStats();
};

// 搜索筛选
const searchForm = ref({
  keyword: "",
  install_type: "",
  is_recommended: "",
  is_enabled: "",
});

// 统计数据
const stats = ref<PluginStatistics>({
  definition_stats: {
    total_count: 0,
    by_type: {},
    recommended_count: 0,
    enabled_count: 0,
  },
  installation_stats: {
    total_count: 0,
    active_count: 0,
    weekly_new_count: 0,
  },
});

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await getPluginStatistics();
    if (response.data) {
      stats.value = response.data;
    }
  } catch (error) {
    console.error("加载统计数据失败:", error);
  }
};

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 截断字符串
function truncateText(text: string, maxLength: number = 30): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
}

// 列定义
const columns: ColumnDef<PluginDefinition>[] = [
  {
    accessorKey: "plugin_id",
    header: "插件信息",
    size: 280,
    cell: ({ row }) => {
      const plugin = row.original;
      const truncatedId = truncateText(plugin.plugin_unique_identifier, 30);
      const isTruncated = plugin.plugin_unique_identifier.length > 30;

      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, plugin.plugin_id),
        isTruncated
          ? h(
              TooltipProvider,
              {},
              () => [
                h(Tooltip, {}, () => [
                  h(TooltipTrigger, { class: "cursor-default" }, () =>
                    h("span", { class: "text-muted-foreground text-xs font-mono" }, truncatedId)
                  ),
                  h(TooltipContent, { side: "bottom", class: "max-w-md" }, () =>
                    h("div", { class: "text-xs font-mono break-all" }, plugin.plugin_unique_identifier)
                  ),
                ]),
              ]
            )
          : h("div", { class: "text-muted-foreground text-xs font-mono" }, truncatedId),
      ]);
    },
  },
  {
    accessorKey: "install_type",
    header: "安装类型",
    size: 100,
    cell: ({ row }) => {
      const type = row.original.install_type;
      return h(Badge, { variant: type === "local" ? "default" : "secondary" }, () => type);
    },
  },
  {
    accessorKey: "is_recommended",
    header: "推荐",
    size: 80,
    cell: ({ row }) => {
      const isRecommended = row.original.is_recommended;
      return h(
        Badge,
        { variant: isRecommended ? "default" : "outline" },
        () => (isRecommended ? "是" : "否")
      );
    },
  },
  {
    accessorKey: "is_enabled",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const isEnabled = row.original.is_enabled;
      return h(
        Badge,
        { variant: isEnabled ? "default" : "secondary" },
        () => (isEnabled ? "启用" : "禁用")
      );
    },
  },
  {
    accessorKey: "refers",
    header: "引用次数",
    size: 100,
    cell: ({ row }) => row.original.refers || 0,
  },
  {
    accessorKey: "created_at",
    header: "创建时间",
    size: 150,
    cell: ({ row }) => formatDate(row.original.created_at),
  },
  {
    id: "actions",
    header: "操作",
    size: 240,
    cell: ({ row }) => {
      const plugin = row.original;
      return h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleDetail(plugin) },
          () => [h(Eye, { class: "mr-1 h-3.5 w-3.5" }), "详情"]
        ),
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleToggleEnabled(plugin) },
          () => [h(CheckCircle, { class: "mr-1 h-3.5 w-3.5" }), plugin.is_enabled ? "禁用" : "启用"]
        ),
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleInstallToTenants(plugin) },
          () => [h(Download, { class: "mr-1 h-3.5 w-3.5" }), "安装"]
        ),
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleEdit(plugin) },
          () => [h(Pencil, { class: "mr-1 h-3.5 w-3.5" }), "编辑"]
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            class: "text-destructive hover:text-destructive",
            onClick: () => handleDelete(plugin),
          },
          () => [h(Trash2, { class: "mr-1 h-3.5 w-3.5" }), "删除"]
        ),
      ]);
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<PluginDefinition>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getPluginDefinitions({
      page,
      page_size,
      keyword: searchForm.value.keyword || undefined,
      type: searchForm.value.install_type || undefined,
      is_recommended:
        searchForm.value.is_recommended === "" || searchForm.value.is_recommended === "all"
          ? undefined
          : searchForm.value.is_recommended === "true",
      is_enabled:
        searchForm.value.is_enabled === "" || searchForm.value.is_enabled === "all"
          ? undefined
          : searchForm.value.is_enabled === "true",
    });
    return response;
  },
});

// 初始化
loadStats();

// 搜索
const handleSearch = () => {
  dataTable.refresh(true);
};

// 重置
const handleReset = () => {
  searchForm.value = { keyword: "", install_type: "", is_recommended: "", is_enabled: "" };
  dataTable.refresh(true);
};

// 查看详情
const handleDetail = (row: PluginDefinition) => {
  router.push(`/admin/plugin-definitions/${row.plugin_id}`);
};

// 编辑
const handleEdit = (row: PluginDefinition) => {
  router.push(`/admin/plugin-definitions/${row.plugin_id}/edit`);
};

// 切换启用状态
const handleToggleEnabled = async (row: PluginDefinition) => {
  const action = row.is_enabled ? "禁用" : "启用";
  if (!(await confirmAction(`确定要${action}插件 "${row.plugin_id}" 吗？`))) return;

  try {
    await updatePluginDefinition(row.plugin_id, { is_enabled: !row.is_enabled });
    notifySuccess(`插件已${action}`);
    dataTable.refresh();
    loadStats();
  } catch (error: any) {
    console.error(`${action}插件失败:`, error);
    const errorMessage = error?.response?.data?.msg || error?.message || `${action}失败`;
    notifyError(errorMessage);
  }
};

// 扫描目录
const handleScan = () => {
  router.push('/admin/plugin-definitions/scan');
};

// 上传插件
const handleUpload = () => {
  router.push('/admin/plugin-definitions/upload');
};

// 删除
const handleDelete = async (row: PluginDefinition) => {
  if (row.refers > 0) {
    notifyError("该插件已被租户安装，无法删除");
    return;
  }
  if (!(await confirmAction('确定要删除插件 "" 吗？删除后不可恢复。'))) return;

  try {
    await deletePluginDefinition(row.plugin_id);
    notifySuccess("插件已删除");
    dataTable.refresh();
    loadStats();
  } catch (error: any) {
    console.error("删除插件失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "删除失败";
    notifyError(errorMessage);
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-definition-list-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold">插件定义</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理系统插件定义，包括插件包注册、版本管理和配置。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" data-testid="refresh-btn" @click="dataTable.refresh()">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button variant="outline" data-testid="scan-btn" @click="handleScan">
          <FolderSearch class="mr-1 h-4 w-4" />
          扫描目录
        </Button>
        <Button variant="outline" data-testid="upload-btn" @click="handleUpload">
          <Upload class="mr-1 h-4 w-4" />
          上传插件
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">插件总数</p>
            <p class="text-2xl font-bold mt-1">{{ stats.definition_stats.total_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">已注册的插件定义数量</p>
          </div>
          <Package class="h-8 w-8 opacity-20 text-blue-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">推荐插件</p>
            <p class="text-2xl font-bold mt-1">{{ stats.definition_stats.recommended_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">标记为推荐的插件数量</p>
          </div>
          <Star class="h-8 w-8 opacity-20 text-amber-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">启用插件</p>
            <p class="text-2xl font-bold mt-1">{{ stats.definition_stats.enabled_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">当前启用状态的插件数量</p>
          </div>
          <CheckCircle class="h-8 w-8 opacity-20 text-green-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">总安装次数</p>
            <p class="text-2xl font-bold mt-1">{{ stats.installation_stats.total_count }}</p>
            <p class="text-xs text-muted-foreground mt-1">所有租户的插件安装总数</p>
          </div>
          <Users class="h-8 w-8 opacity-20 text-indigo-500" />
        </div>
      </div>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <div class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">插件列表</div>
            <div class="text-muted-foreground mt-1 text-xs">管理系统插件定义</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Input
              v-model="searchForm.keyword"
              class="w-56"
              placeholder="搜索插件 ID"
              data-testid="search-keyword-input"
              @keydown.enter="handleSearch"
            />
            <Select v-model="searchForm.install_type">
              <SelectTrigger class="w-[120px]" data-testid="type-select">
                <SelectValue placeholder="安装类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="local">本地</SelectItem>
                <SelectItem value="remote">远程</SelectItem>
              </SelectContent>
            </Select>
            <Select v-model="searchForm.is_enabled">
              <SelectTrigger class="w-[120px]" data-testid="status-select">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="true">启用</SelectItem>
                <SelectItem value="false">禁用</SelectItem>
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
        <DataTable data-testid="plugin-table" :data-table="dataTable" :fixed-layout="true" />
      </div>
    </div>
    <InstallToTenantsDialog
      :plugin="installTargetPlugin"
      :open="installDialogOpen"
      @update:open="installDialogOpen = $event"
      @installed="handleInstalled"
    />
  </div>
</template>

