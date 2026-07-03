<script setup lang="ts">
import {
  ArrowLeft,
  Search,
  RotateCcw,
  Download,
  Package,
  CheckCircle,
  Loader2,
  ExternalLink,
} from "@lucide/vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { h, ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Badge, Button, Card, DataTable, Input, useDataTable } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { notifyError, notifySuccess } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import {
  getMarketplace,
  getRemotePlugins,
  syncPlugins,
} from "@/tenant/api/marketplace";
import type { Marketplace, RemotePlugin } from "@/tenant/types/marketplace";

const route = useRoute();
const router = useRouter();

const marketplaceId = computed(() => route.params.id as string);

// 市场信息
const marketplace = ref<Marketplace | null>(null);
const loadingMarketplace = ref(false);

// 搜索筛选
const searchForm = ref({
  keyword: "",
  type: "",
});

// 选中的插件 (plugin_id -> plugin_type)
const selectedPluginIds = ref<Map<string, string>>(new Map());
const isSyncing = ref(false);

// 加载市场信息
const loadMarketplace = async () => {
  loadingMarketplace.value = true;
  try {
    const response = await getMarketplace(marketplaceId.value);
    if (response.data) {
      marketplace.value = response.data;
    }
  } catch (error) {
    console.error("加载市场信息失败:", error);
    notifyError("加载市场信息失败");
  } finally {
    loadingMarketplace.value = false;
  }
};

// 格式化数字
function formatNumber(num?: number): string {
  if (!num) return "0";
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}

// 获取插件类型标签
function getTypeLabel(type: string): string {
  switch (type) {
    case "tool":
      return "工具";
    case "model":
      return "模型";
    case "agent":
      return "Agent";
    case "extension":
      return "扩展";
    default:
      return type;
  }
}

// 列定义
const columns: ColumnDef<RemotePlugin>[] = [
  {
    id: "selection",
    header: () => h("input", {
      type: "checkbox",
      class: "cursor-pointer",
      checked: selectedPluginIds.value.size > 0,
      onChange: (e: Event) => {
        const target = e.target as HTMLInputElement;
        if (target.checked) {
          // 全选当前页
          // Note: 实际实现需要访问当前页数据
        } else {
          selectedPluginIds.value.clear();
        }
      },
    }),
    size: 40,
    cell: ({ row }) => {
      const plugin = row.original;
      return h("input", {
        type: "checkbox",
        class: "cursor-pointer",
        checked: selectedPluginIds.value.has(plugin.plugin_id),
        onChange: (e: Event) => {
          const target = e.target as HTMLInputElement;
          if (target.checked) {
            selectedPluginIds.value.set(plugin.plugin_id, plugin.plugin_type);
          } else {
            selectedPluginIds.value.delete(plugin.plugin_id);
          }
        },
      });
    },
  },
  {
    accessorKey: "plugin_id",
    header: "插件信息",
    size: 280,
    cell: ({ row }) => {
      const plugin = row.original;
      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, plugin.name || plugin.plugin_id),
        h("div", { class: "text-muted-foreground text-xs font-mono" }, plugin.plugin_id),
      ]);
    },
  },
  {
    accessorKey: "version",
    header: "版本",
    size: 80,
    cell: ({ row }) => h("span", { class: "text-xs font-mono" }, `v${row.original.version}`),
  },
  {
    accessorKey: "plugin_type",
    header: "类型",
    size: 100,
    cell: ({ row }) => {
      const type = row.original.plugin_type;
      return h(Badge, { variant: "secondary" }, () => getTypeLabel(type));
    },
  },
  {
    accessorKey: "author",
    header: "作者",
    size: 120,
    cell: ({ row }) => row.original.author,
  },
  {
    accessorKey: "downloads",
    header: "下载量",
    size: 100,
    cell: ({ row }) => {
      const downloads = row.original.downloads || 0;
      return h("div", { class: "flex items-center gap-1" }, [
        h(Download, { class: "h-3.5 w-3.5 text-muted-foreground" }),
        h("span", {}, formatNumber(downloads)),
      ]);
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 100,
    cell: ({ row }) => {
      const plugin = row.original;
      return h(
        Button,
        {
          variant: "ghost",
          size: "sm",
          onClick: () => handleSyncSingle(plugin),
        },
        () => [h(Download, { class: "mr-1 h-3.5 w-3.5" }), "同步"]
      );
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<RemotePlugin>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getRemotePlugins(marketplaceId.value, {
      page,
      page_size,
      keyword: searchForm.value.keyword || undefined,
      type: searchForm.value.type || undefined,
    });
    return createPaginatedResponse({
      code: response.code,
      msg: response.msg,
      data: response.data || [],
      total: response.data?.length || 0,
      page,
      page_size,
    });
  },
});

// 初始化
onMounted(() => {
  loadMarketplace();
});

// 搜索
const handleSearch = () => {
  dataTable.refresh(true);
};

// 重置
const handleReset = () => {
  searchForm.value = { keyword: "", type: "" };
  selectedPluginIds.value.clear();
  dataTable.refresh(true);
};

// 同步单个插件
const handleSyncSingle = async (plugin: RemotePlugin) => {
  try {
    const response = await syncPlugins({
      marketplace_id: marketplaceId.value,
      plugins: [{ plugin_id: plugin.plugin_id, plugin_type: plugin.plugin_type }],
    });
    if (response.data) {
      if (response.data.success.length > 0) {
        notifySuccess(`插件 ${plugin.name} 同步成功`);
      } else if (response.data.skipped.length > 0) {
        notifySuccess(`插件 ${plugin.name} 已存在，跳过同步`);
      } else if (response.data.failed.length > 0) {
        notifyError(`同步失败: ${response.data.failed[0].message}`);
      }
    }
  } catch (error: any) {
    console.error("同步插件失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "同步失败";
    notifyError(errorMessage);
  }
};

// 批量同步选中插件
const handleSyncSelected = async () => {
  if (selectedPluginIds.value.size === 0) {
    notifyError("请先选择要同步的插件");
    return;
  }

  isSyncing.value = true;
  try {
    const plugins = Array.from(selectedPluginIds.value.entries()).map(([plugin_id, plugin_type]) => ({
      plugin_id,
      plugin_type,
    }));
    const response = await syncPlugins({
      marketplace_id: marketplaceId.value,
      plugins,
    });
    if (response.data) {
      const { success, failed, skipped } = response.data;
      notifySuccess(`同步完成: 成功 ${success.length} 个，跳过 ${skipped.length} 个，失败 ${failed.length} 个`);
      selectedPluginIds.value.clear();
    }
  } catch (error: any) {
    console.error("批量同步插件失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "同步失败";
    notifyError(errorMessage);
  } finally {
    isSyncing.value = false;
  }
};

// 返回市场列表
const handleBack = () => {
  router.push("/admin/marketplaces");
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="remote-plugin-browse-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" data-testid="back-btn" @click="handleBack">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold">
            {{ marketplace?.name || "远程插件" }}
          </h2>
          <p class="text-muted-foreground mt-1 text-sm">
            浏览市场中的插件并同步到本地
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          :disabled="selectedPluginIds.size === 0 || isSyncing"
          data-testid="sync-selected-btn"
          @click="handleSyncSelected"
        >
          <Loader2 v-if="isSyncing" class="mr-1 h-4 w-4 animate-spin" />
          <CheckCircle v-else class="mr-1 h-4 w-4" />
          {{ isSyncing ? "同步中..." : `同步选中 (${selectedPluginIds.size})` }}
        </Button>
      </div>
    </div>

    <!-- 市场信息卡片 -->
    <div v-if="marketplace" class="grid gap-4 md:grid-cols-3">
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center gap-3">
          <Package class="h-8 w-8 opacity-20 text-blue-500" />
          <div>
            <p class="text-sm text-muted-foreground">市场类型</p>
            <p class="font-medium">{{ marketplace.type === "official" ? "官方市场" : marketplace.type === "community" ? "社区市场" : "私有市场" }}</p>
          </div>
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center gap-3">
          <ExternalLink class="h-8 w-8 opacity-20 text-green-500" />
          <div>
            <p class="text-sm text-muted-foreground">市场地址</p>
            <p class="font-medium text-xs font-mono truncate" :title="marketplace.url">
              {{ marketplace.url }}
            </p>
          </div>
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center gap-3">
          <CheckCircle class="h-8 w-8 opacity-20" :class="marketplace.is_enabled ? 'text-green-500' : 'text-gray-500'" />
          <div>
            <p class="text-sm text-muted-foreground">状态</p>
            <Badge :variant="marketplace.is_enabled ? 'default' : 'secondary'">
              {{ marketplace.is_enabled ? "已启用" : "已禁用" }}
            </Badge>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <div class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">远程插件列表</div>
            <div class="text-muted-foreground mt-1 text-xs">选择插件同步到本地插件定义</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Input
              v-model="searchForm.keyword"
              class="w-56"
              placeholder="搜索插件名称或 ID"
              data-testid="search-keyword-input"
              @keydown.enter="handleSearch"
            />
            <Select v-model="searchForm.type">
              <SelectTrigger class="w-[120px]" data-testid="type-select">
                <SelectValue placeholder="插件类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="tool">工具</SelectItem>
                <SelectItem value="model">模型</SelectItem>
                <SelectItem value="agent">Agent</SelectItem>
                <SelectItem value="extension">扩展</SelectItem>
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
        <DataTable data-testid="remote-plugin-table" :data-table="dataTable" :fixed-layout="true" />
      </div>
    </div>
  </div>
</template>
