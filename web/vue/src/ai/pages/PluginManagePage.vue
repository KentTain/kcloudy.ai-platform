<script setup lang="ts">
/**
 * 插件管理页面
 *
 * 统一显示可安装和已安装的插件，类似应用商店的设计
 */
import { ref, h, computed, onMounted } from "vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { Badge, Button, Input, DataTable, useDataTable, Card } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import {
  getAvailablePlugins,
  createPluginInstallation,
  type AvailablePlugin,
} from "@/ai/api/plugin";
import { startPlugin, stopPlugin } from "@/ai/api/pluginConfig";
import {
  Search,
  RefreshCw,
  Download,
  Check,
  Loader2,
  Package,
  Sparkles,
  Settings,
  Play,
  Square,
} from "lucide-vue-next";
import { useRouter } from "vue-router";

const router = useRouter();

// 搜索筛选
const searchForm = ref({
  keyword: "",
  plugin_type: "all",
  status: "all", // all, installed, not_installed
});

// 安装中的插件ID集合
const installingPlugins = ref<Set<string>>(new Set());

// 启停中的插件ID集合
const operatingPlugins = ref<Set<string>>(new Set());

// 统计数据
const statistics = ref({
  total: 0,
  installed: 0,
  recommended: 0,
});

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 状态颜色映射
const statusColorMap: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  INSTALLED: "default",
  ACTIVE: "default",
  INACTIVE: "outline",
  PENDING: "outline",
  INSTALLING: "outline",
  FAILED: "destructive",
};

// 状态文本映射
const statusTextMap: Record<string, string> = {
  INSTALLED: "已安装",
  ACTIVE: "运行中",
  INACTIVE: "已停止",
  PENDING: "待安装",
  INSTALLING: "安装中",
  FAILED: "安装失败",
};

// 类型文本映射
const typeTextMap: Record<string, string> = {
  model: "模型",
  tool: "工具",
  agent: "代理",
  unknown: "未知",
};

// 列定义
const columns: ColumnDef<AvailablePlugin>[] = [
  {
    accessorKey: "plugin_id",
    header: "插件信息",
    size: 300,
    cell: ({ row }) => {
      const plugin = row.original;
      return h("div", { class: "flex items-center gap-3" }, [
        plugin.icon
          ? h("img", {
              src: plugin.icon,
              class: "w-12 h-12 rounded-lg object-cover",
              alt: plugin.name,
            })
          : h(
              "div",
              {
                class:
                  "w-12 h-12 rounded-lg bg-muted flex items-center justify-center",
              },
              h(Package, { class: "w-6 h-6 text-muted-foreground" })
            ),
        h("div", { class: "space-y-1 flex-1 min-w-0" }, [
          h("div", { class: "flex items-center gap-2" }, [
            h(
              "span",
              { class: "font-medium truncate" },
              plugin.name || plugin.plugin_id.split("/").pop()
            ),
            plugin.is_recommended
              ? h(
                  Badge,
                  { variant: "outline", class: "text-xs" },
                  () => "推荐"
                )
              : null,
          ]),
          h(
            "div",
            { class: "text-muted-foreground text-xs truncate" },
            plugin.plugin_id
          ),
          plugin.description
            ? h(
                "div",
                { class: "text-muted-foreground text-xs truncate max-w-[400px]" },
                plugin.description
              )
            : null,
        ]),
      ]);
    },
  },
  {
    accessorKey: "plugin_type",
    header: "类型",
    size: 80,
    cell: ({ row }) => {
      const type = row.original.plugin_type;
      return h(Badge, { variant: "outline" }, () => typeTextMap[type] || type);
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
    accessorKey: "status",
    header: "状态",
    size: 120,
    cell: ({ row }) => {
      const plugin = row.original;
      if (plugin.is_installed) {
        const status = plugin.installation_status || "INSTALLED";
        return h("div", { class: "flex flex-col gap-1" }, [
          h(
            Badge,
            { variant: statusColorMap[status] || "outline" },
            () => statusTextMap[status] || status
          ),
        ]);
      }
      return h(Badge, { variant: "secondary" }, () => "未安装");
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 200,
    cell: ({ row }) => {
      const plugin = row.original;
      const isInstalling = installingPlugins.value.has(plugin.plugin_id);
      const isOperating = operatingPlugins.value.has(plugin.plugin_id);

      if (plugin.is_installed) {
        const status = plugin.installation_status || "INSTALLED";
        const isActive = status === "ACTIVE";
        const isInactive = status === "INACTIVE";

        const actionButtons = [
          h(
            Button,
            {
              variant: "ghost",
              size: "sm",
              onClick: () => handleConfig(plugin),
            },
            () => [h(Settings, { class: "mr-1 h-3.5 w-3.5" }), "配置"]
          ),
        ];

        if (isActive) {
          actionButtons.push(
            h(
              Button,
              {
                variant: "ghost",
                size: "sm",
                disabled: isOperating,
                onClick: () => handleStop(plugin),
              },
              () =>
                isOperating
                  ? [h(Loader2, { class: "mr-1 h-3.5 w-3.5 animate-spin" }), "停止中"]
                  : [h(Square, { class: "mr-1 h-3.5 w-3.5" }), "停止"]
            )
          );
        } else if (isInactive) {
          actionButtons.push(
            h(
              Button,
              {
                variant: "ghost",
                size: "sm",
                disabled: isOperating,
                onClick: () => handleStart(plugin),
              },
              () =>
                isOperating
                  ? [h(Loader2, { class: "mr-1 h-3.5 w-3.5 animate-spin" }), "启动中"]
                  : [h(Play, { class: "mr-1 h-3.5 w-3.5" }), "启动"]
            )
          );
        } else {
          actionButtons.push(
            h(
              Button,
              {
                variant: "outline",
                size: "sm",
                disabled: true,
              },
              () => [h(Check, { class: "mr-1 h-3.5 w-3.5" }), statusTextMap[status] || status]
            )
          );
        }

        return h("div", { class: "flex items-center gap-1" }, actionButtons);
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
      type:
        searchForm.value.plugin_type === "all"
          ? undefined
          : searchForm.value.plugin_type,
    });

    // 更新统计数据
    if (response.code === 200) {
      const items = response.data || [];
      statistics.value = {
        total: response.total || 0,
        installed: items.filter((p) => p.is_installed).length,
        recommended: items.filter((p) => p.is_recommended).length,
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
  searchForm.value = { keyword: "", plugin_type: "all", status: "all" };
  dataTable.refresh(true);
};

// 刷新列表
const handleRefresh = () => {
  dataTable.refresh();
};

// 查看配置
const handleConfig = (plugin: AvailablePlugin) => {
  router.push(`/ai/plugins/${encodeURIComponent(plugin.plugin_id)}/config`);
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
      dataTable.refresh();
    } else {
      notifyError(response.msg || "安装失败");
    }
  } catch (error: any) {
    console.error("安装插件失败:", error);
    const errorMessage =
      error?.response?.data?.msg || error?.message || "安装失败";
    notifyError(errorMessage);
  } finally {
    installingPlugins.value.delete(plugin.plugin_id);
  }
};

// 启动插件
const handleStart = async (plugin: AvailablePlugin) => {
  operatingPlugins.value.add(plugin.plugin_id);

  try {
    const response = await startPlugin(plugin.plugin_id);
    if (response.code === 200) {
      const warning = response.data?.warning;
      if (warning) {
        notifySuccess(`插件 "${plugin.name}" 已启动（${warning}）`);
      } else {
        notifySuccess(`插件 "${plugin.name}" 已启动`);
      }
      dataTable.refresh();
    } else {
      notifyError(response.msg || "启动失败");
    }
  } catch (error: any) {
    console.error("启动插件失败:", error);
    const errorMessage =
      error?.response?.data?.msg || error?.message || "启动失败";
    notifyError(errorMessage);
  } finally {
    operatingPlugins.value.delete(plugin.plugin_id);
  }
};

// 停止插件
const handleStop = async (plugin: AvailablePlugin) => {
  operatingPlugins.value.add(plugin.plugin_id);

  try {
    const response = await stopPlugin(plugin.plugin_id);
    if (response.code === 200) {
      notifySuccess(`插件 "${plugin.name}" 已停止`);
      dataTable.refresh();
    } else {
      notifyError(response.msg || "停止失败");
    }
  } catch (error: any) {
    console.error("停止插件失败:", error);
    const errorMessage =
      error?.response?.data?.msg || error?.message || "停止失败";
    notifyError(errorMessage);
  } finally {
    operatingPlugins.value.delete(plugin.plugin_id);
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-manage-page">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-3 gap-4">
      <Card class="p-4">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10"
          >
            <Package class="h-6 w-6 text-primary" />
          </div>
          <div>
            <div class="text-2xl font-bold">{{ statistics.total }}</div>
            <div class="text-sm text-muted-foreground">总插件</div>
          </div>
        </div>
      </Card>
      <Card class="p-4">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/10"
          >
            <Check class="h-6 w-6 text-green-500" />
          </div>
          <div>
            <div class="text-2xl font-bold">{{ statistics.installed }}</div>
            <div class="text-sm text-muted-foreground">已安装</div>
          </div>
        </div>
      </Card>
      <Card class="p-4">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-500/10"
          >
            <Sparkles class="h-6 w-6 text-amber-500" />
          </div>
          <div>
            <div class="text-2xl font-bold">{{ statistics.recommended }}</div>
            <div class="text-sm text-muted-foreground">推荐插件</div>
          </div>
        </div>
      </Card>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <div class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">插件列表</div>
            <div class="text-muted-foreground mt-1 text-xs">安装和管理插件</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <div class="relative">
              <Search
                class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground"
              />
              <Input
                v-model="searchForm.keyword"
                placeholder="搜索插件..."
                class="w-56 pl-8"
                @keyup.enter="handleSearch"
              />
            </div>
            <Select v-model="searchForm.plugin_type" @update:model-value="handleSearch">
              <SelectTrigger class="w-[120px]">
                <SelectValue placeholder="类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="model">模型</SelectItem>
                <SelectItem value="tool">工具</SelectItem>
                <SelectItem value="agent">代理</SelectItem>
              </SelectContent>
            </Select>
            <Select v-model="searchForm.status" @update:model-value="handleSearch">
              <SelectTrigger class="w-[120px]">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="installed">已安装</SelectItem>
                <SelectItem value="not_installed">未安装</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" @click="handleSearch">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="outline" size="sm" @click="handleReset">重置</Button>
            <Button variant="outline" size="sm" @click="handleRefresh">
              <RefreshCw class="mr-1 h-4 w-4" />
              刷新
            </Button>
          </div>
        </div>
      </div>

      <div class="flex min-h-0 flex-1 flex-col px-5 pt-4">
        <DataTable :data-table="dataTable" :fixed-layout="true" />
      </div>
    </div>
  </div>
</template>
