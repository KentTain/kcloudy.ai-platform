<script setup lang="ts">
import { ref, h, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDataTable } from "@/framework/composables/useDataTable";
import type { ColumnDef } from "@/framework/composables/useDataTable";
import { notifySuccess, notifyError, confirmAction } from "@/framework/utils/feedback";
import {
  getPluginList,
  startPlugin,
  stopPlugin,
  uninstallPlugin,
  type PluginInfo,
} from "@/ai/api/plugin";
import { Play, Square, Trash2, RefreshCw, Search, Package } from "lucide-vue-next";

const router = useRouter();

// 搜索筛选
const searchForm = ref({
  keyword: "",
  status: "",
  plugin_type: "",
});

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 状态颜色映射
const statusColorMap: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  running: "default",
  stopped: "secondary",
  error: "destructive",
  pending: "outline",
};

// 状态文本映射
const statusTextMap: Record<string, string> = {
  running: "运行中",
  stopped: "已停止",
  error: "错误",
  pending: "待启动",
};

// 列定义
const columns: ColumnDef<PluginInfo>[] = [
  {
    accessorKey: "plugin_id",
    header: "插件信息",
    size: 280,
    cell: ({ row }) => {
      const plugin = row.original;
      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, plugin.plugin_id),
        h("div", { class: "text-muted-foreground text-xs" }, plugin.plugin_name),
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
    accessorKey: "runtime_type",
    header: "运行时",
    size: 80,
  },
  {
    accessorKey: "auto_start",
    header: "自动启动",
    size: 80,
    cell: ({ row }) => {
      const autoStart = row.original.auto_start;
      return h(Badge, { variant: autoStart ? "default" : "secondary" }, () => autoStart ? "是" : "否");
    },
  },
  {
    accessorKey: "call_count",
    header: "调用次数",
    size: 80,
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
    size: 200,
    cell: ({ row }) => {
      const plugin = row.original;
      const isRunning = plugin.status === "running";
      return h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            onClick: () => handleStartStop(plugin),
            disabled: plugin.status === "pending",
          },
          () => isRunning
            ? [h(Square, { class: "mr-1 h-3.5 w-3.5" }), "停止"]
            : [h(Play, { class: "mr-1 h-3.5 w-3.5" }), "启动"]
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            class: "text-destructive hover:text-destructive",
            onClick: () => handleUninstall(plugin),
          },
          () => [h(Trash2, { class: "mr-1 h-3.5 w-3.5" }), "卸载"]
        ),
      ]);
    },
  },
];

// 初始化 DataTable
const dataTable = useDataTable<PluginInfo>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getPluginList({
      limit: page_size,
      offset: (page - 1) * page_size,
      plugin_id: searchForm.value.keyword || undefined,
      status: searchForm.value.status || undefined,
      plugin_type: searchForm.value.plugin_type || undefined,
    });
    // 后端返回的是 { plugins: PluginInfo[] }，需要转换为分页格式
    const plugins = response.data?.plugins || [];
    return {
      data: plugins,
      total: plugins.length,
      page,
      page_size,
    };
  },
});

// 搜索
const handleSearch = () => {
  dataTable.refresh(true);
};

// 重置
const handleReset = () => {
  searchForm.value = { keyword: "", status: "", plugin_type: "" };
  dataTable.refresh(true);
};

// 刷新列表
const handleRefresh = () => {
  dataTable.refresh();
};

// 启动/停止插件
const handleStartStop = async (plugin: PluginInfo) => {
  const isRunning = plugin.status === "running";
  const action = isRunning ? "停止" : "启动";
  
  if (!(await confirmAction(`确定要${action}插件 "${plugin.plugin_id}" 吗？`))) return;

  try {
    const response = isRunning
      ? await stopPlugin(plugin.plugin_id)
      : await startPlugin(plugin.plugin_id);
    
    if (response.code === 200) {
      notifySuccess(response.data?.message || `插件已${action}`);
      dataTable.refresh();
    } else {
      notifyError(response.msg || `${action}失败`);
    }
  } catch (error: any) {
    console.error(`${action}插件失败:`, error);
    const errorMessage = error?.response?.data?.msg || error?.message || `${action}失败`;
    notifyError(errorMessage);
  }
};

// 卸载插件
const handleUninstall = async (plugin: PluginInfo) => {
  if (!(await confirmAction(`确定要卸载插件 "${plugin.plugin_id}" 吗？此操作不可恢复。`))) return;

  try {
    const response = await uninstallPlugin(plugin.plugin_id);
    if (response.code === 200) {
      notifySuccess(response.data?.message || "插件已卸载");
      dataTable.refresh();
    } else {
      notifyError(response.msg || "卸载失败");
    }
  } catch (error: any) {
    console.error("卸载插件失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "卸载失败";
    notifyError(errorMessage);
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-list-page">
    <!-- 搜索区域 -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1">
        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          v-model="searchForm.keyword"
          placeholder="搜索插件 ID..."
          class="pl-8"
          @keyup.enter="handleSearch"
        />
      </div>
      <Select v-model="searchForm.status" @update:model-value="handleSearch">
        <SelectTrigger class="w-[140px]">
          <SelectValue placeholder="状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">全部状态</SelectItem>
          <SelectItem value="running">运行中</SelectItem>
          <SelectItem value="stopped">已停止</SelectItem>
          <SelectItem value="error">错误</SelectItem>
          <SelectItem value="pending">待启动</SelectItem>
        </SelectContent>
      </Select>
      <Select v-model="searchForm.plugin_type" @update:model-value="handleSearch">
        <SelectTrigger class="w-[140px]">
          <SelectValue placeholder="类型" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">全部类型</SelectItem>
          <SelectItem value="model">模型</SelectItem>
          <SelectItem value="tool">工具</SelectItem>
          <SelectItem value="endpoint">端点</SelectItem>
          <SelectItem value="agent">代理</SelectItem>
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
      <dataTable.DataTable />
    </div>

    <!-- 分页 -->
    <dataTable.Pagination />
  </div>
</template>
