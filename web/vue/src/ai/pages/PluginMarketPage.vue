<script setup lang="ts">
/**
 * 插件市场页面
 *
 * 显示所有可安装的插件定义，支持安装操作
 */
import { ref, h, onMounted, computed } from "vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { Badge, Button, Input, DataTable, useDataTable } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import { getAvailablePlugins, createPluginInstallation, type AvailablePlugin } from "@/ai/api/plugin";
import { Search, RefreshCw, Download, Check, Loader2 } from "lucide-vue-next";

// 搜索筛选
const searchForm = ref({
  keyword: "",
  plugin_type: "all",
  is_recommended: "all",
});

// 安装中的插件ID集合
const installingPlugins = ref<Set<string>>(new Set());

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 状态颜色映射
const statusColorMap: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  INSTALLED: "default",
  PENDING: "outline",
  INSTALLING: "outline",
  FAILED: "destructive",
};

// 状态文本映射
const statusTextMap: Record<string, string> = {
  INSTALLED: "已安装",
  PENDING: "待安装",
  INSTALLING: "安装中",
  FAILED: "安装失败",
};

// 列定义
const columns: ColumnDef<AvailablePlugin>[] = [
  {
    accessorKey: "plugin_id",
    header: "插件信息",
    size: 280,
    cell: ({ row }) => {
      const plugin = row.original;
      return h("div", { class: "flex items-center gap-3" }, [
        plugin.icon
          ? h("img", { src: plugin.icon, class: "w-10 h-10 rounded", alt: plugin.name })
          : h("div", { class: "w-10 h-10 rounded bg-muted flex items-center justify-center" }, "📦"),
        h("div", { class: "space-y-1" }, [
          h("div", { class: "font-medium" }, plugin.name || plugin.plugin_id.split("/").pop()),
          h("div", { class: "text-muted-foreground text-xs" }, plugin.plugin_id),
        ]),
      ]);
    },
  },
  {
    accessorKey: "version",
    header: "版本",
    size: 80,
  },
  {
    accessorKey: "author",
    header: "作者",
    size: 100,
  },
  {
    accessorKey: "plugin_type",
    header: "类型",
    size: 100,
    cell: ({ row }) => {
      const type = row.original.plugin_type;
      const typeTextMap: Record<string, string> = {
        model: "模型",
        tool: "工具",
        agent: "代理",
        unknown: "未知",
      };
      return h(Badge, { variant: "outline" }, () => typeTextMap[type] || type);
    },
  },
  {
    accessorKey: "is_recommended",
    header: "推荐",
    size: 80,
    cell: ({ row }) => {
      const isRecommended = row.original.is_recommended;
      return isRecommended
        ? h(Badge, { variant: "default" }, () => "推荐")
        : null;
    },
  },
  {
    accessorKey: "is_installed",
    header: "状态",
    size: 100,
    cell: ({ row }) => {
      const plugin = row.original;
      if (plugin.is_installed) {
        const status = plugin.installation_status || "INSTALLED";
        return h(
          Badge,
          { variant: statusColorMap[status] || "outline" },
          () => statusTextMap[status] || status
        );
      }
      return h(Badge, { variant: "secondary" }, () => "未安装");
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 120,
    cell: ({ row }) => {
      const plugin = row.original;
      const isInstalling = installingPlugins.value.has(plugin.plugin_id);

      if (plugin.is_installed) {
        return h(
          Button,
          {
            variant: "outline",
            size: "sm",
            disabled: true,
          },
          () => [h(Check, { class: "mr-1 h-3.5 w-3.5" }), "已安装"]
        );
      }

      return h(
        Button,
        {
          variant: "default",
          size: "sm",
          disabled: isInstalling,
          onClick: () => handleInstall(plugin),
        },
        () =>
          isInstalling
            ? [h(Loader2, { class: "mr-1 h-3.5 w-3.5 animate-spin" }), "安装中"]
            : [h(Download, { class: "mr-1 h-3.5 w-3.5" }), "安装"]
      );
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<AvailablePlugin>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getAvailablePlugins({
      page,
      page_size,
      keyword: searchForm.value.keyword || undefined,
      type: searchForm.value.plugin_type === "all" ? undefined : searchForm.value.plugin_type,
      is_recommended:
        searchForm.value.is_recommended === "all"
          ? undefined
          : searchForm.value.is_recommended === "true",
    });
    return response;
  },
});

// 搜索
const handleSearch = () => {
  dataTable.refresh(true);
};

// 重置
const handleReset = () => {
  searchForm.value = { keyword: "", plugin_type: "all", is_recommended: "all" };
  dataTable.refresh(true);
};

// 刷新列表
const handleRefresh = () => {
  dataTable.refresh();
};

// 安装插件
const handleInstall = async (plugin: AvailablePlugin) => {
  installingPlugins.value.add(plugin.plugin_id);

  try {
    const response = await createPluginInstallation({
      plugin_id: plugin.plugin_id,
      auto_start: true,
    });

    if (response.code === 200) {
      notifySuccess(`插件 "${plugin.name}" 安装任务已创建`);
      // 跳转到任务详情或刷新列表
      dataTable.refresh();
    } else {
      notifyError(response.msg || "安装失败");
    }
  } catch (error: any) {
    console.error("安装插件失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "安装失败";
    notifyError(errorMessage);
  } finally {
    installingPlugins.value.delete(plugin.plugin_id);
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-market-page">
    <!-- 搜索区域 -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1">
        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          v-model="searchForm.keyword"
          placeholder="搜索插件..."
          class="pl-8"
          @keyup.enter="handleSearch"
        />
      </div>
      <Select v-model="searchForm.plugin_type" @update:model-value="handleSearch">
        <SelectTrigger class="w-[140px]">
          <SelectValue placeholder="类型" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部类型</SelectItem>
          <SelectItem value="model">模型</SelectItem>
          <SelectItem value="tool">工具</SelectItem>
          <SelectItem value="agent">代理</SelectItem>
        </SelectContent>
      </Select>
      <Select v-model="searchForm.is_recommended" @update:model-value="handleSearch">
        <SelectTrigger class="w-[140px]">
          <SelectValue placeholder="推荐" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部</SelectItem>
          <SelectItem value="true">推荐</SelectItem>
          <SelectItem value="false">非推荐</SelectItem>
        </SelectContent>
      </Select>
      <Button @click="handleSearch">
        <Search class="mr-2 h-4 w-4" />
        搜索
      </Button>
      <Button variant="outline" @click="handleReset">重置</Button>
      <Button variant="outline" @click="handleRefresh">
        <RefreshCw class="mr-2 h-4 w-4" />
        刷新
      </Button>
    </div>

    <!-- 数据表格 -->
    <div class="flex-1 overflow-auto rounded-md border">
      <DataTable :data-table="dataTable" />
    </div>
  </div>
</template>
