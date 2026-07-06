<script setup lang="ts">
import {
  Plus,
  RefreshCw,
  Pencil,
  Trash2,
  ExternalLink,
  Wifi,
  Globe,
  Server,
  CheckCircle,
  XCircle,
  Clock,
} from "@lucide/vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { h, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Badge, Button, Card, DataTable, useDataTable } from "@/components";
import { confirmAction, notifyError, notifySuccess } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import {
  checkUpdates,
  getMarketplaces,
  deleteMarketplace,
  testMarketplace,
} from "@/tenant/api/marketplace";
import type { Marketplace, MarketplaceTestResult, PluginUpdateInfo } from "@/tenant/types/marketplace";

const router = useRouter();

// 测试结果缓存
const testResults = ref<Map<string, MarketplaceTestResult>>(new Map());
const testingIds = ref<Set<string>>(new Set());

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

// 获取市场类型图标
function getTypeIcon(type: string) {
  if (type.startsWith("local")) return Server;
  if (type === "dify" || type === "agentskills") return CheckCircle;
  return Globe;
}

// 获取市场类型标签
const typeLabelMap: Record<string, string> = {
  dify: "Dify 市场",
  modelscope: "ModelScope 市场",
  agentskills: "AgentSkills 市场",
  "modelscope-skill": "ModelScope Skill",
  "local-skill": "本地 Skill 目录",
  "local-plugin": "本地 Plugin 目录",
};

function getTypeLabel(type: string): string {
  return typeLabelMap[type] || type;
}

// 列定义
const columns: ColumnDef<Marketplace>[] = [
  {
    accessorKey: "name",
    header: "市场名称",
    size: 200,
    cell: ({ row }) => {
      const marketplace = row.original;
      return h("div", { class: "space-y-1" }, [
        h("div", { class: "font-medium" }, marketplace.name),
        h("div", { class: "text-muted-foreground text-xs font-mono" }, marketplace.code),
      ]);
    },
  },
  {
    accessorKey: "type",
    header: "类型",
    size: 100,
    cell: ({ row }) => {
      const type = row.original.type;
      const IconComponent = getTypeIcon(type);
      return h("div", { class: "flex items-center gap-2" }, [
        h(IconComponent, { class: "h-4 w-4" }),
        h("span", {}, getTypeLabel(type)),
      ]);
    },
  },
  {
    accessorKey: "url",
    header: "市场地址",
    size: 280,
    cell: ({ row }) => {
      const url = row.original.url;
      const truncatedUrl = url && url.length > 40 ? url.slice(0, 40) + "..." : url;
      return h("div", { class: "text-xs font-mono text-muted-foreground", title: url }, truncatedUrl || "--");
    },
  },
  {
    accessorKey: "is_enabled",
    header: "状态",
    size: 100,
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
    accessorKey: "last_sync_at",
    header: "最后同步",
    size: 160,
    cell: ({ row }) => {
      const marketplace = row.original;
      if (!marketplace.last_sync_at) {
        return h("span", { class: "text-muted-foreground" }, "从未同步");
      }
      const syncStatus = marketplace.last_sync_status;
      const statusIcon = syncStatus === "success"
        ? h(CheckCircle, { class: "h-3.5 w-3.5 text-green-500 mr-1" })
        : syncStatus === "failed"
          ? h(XCircle, { class: "h-3.5 w-3.5 text-red-500 mr-1" })
          : null;
      return h("div", { class: "flex items-center" }, [
        statusIcon,
        h("span", {}, formatDate(marketplace.last_sync_at)),
      ]);
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 280,
    cell: ({ row }) => {
      const marketplace = row.original;
      const isTesting = testingIds.value.has(marketplace.id);
      const testResult = testResults.value.get(marketplace.id);

      return h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            onClick: () => handleBrowse(marketplace),
            disabled: !marketplace.is_enabled,
          },
          () => [h(ExternalLink, { class: "mr-1 h-3.5 w-3.5" }), "浏览"]
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            onClick: () => handleCheckUpdates(marketplace),
            disabled: !marketplace.is_enabled,
          },
          () => [h(RefreshCw, { class: "mr-1 h-3.5 w-3.5" }), "检查更新"]
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            onClick: () => handleTest(marketplace),
            disabled: isTesting,
          },
          () => [
            isTesting
              ? h(Clock, { class: "mr-1 h-3.5 w-3.5 animate-spin" })
              : h(Wifi, { class: "mr-1 h-3.5 w-3.5" }),
            testResult?.success ? "正常" : "测试",
          ]
        ),
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleEdit(marketplace) },
          () => [h(Pencil, { class: "mr-1 h-3.5 w-3.5" }), "编辑"]
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            class: "text-destructive hover:text-destructive",
            onClick: () => handleDelete(marketplace),
          },
          () => [h(Trash2, { class: "mr-1 h-3.5 w-3.5" }), "删除"]
        ),
      ]);
    },
  },
];

// 初始化 DataTable - 市场列表不支持分页，直接获取全部
const dataTable = useDataTable<Marketplace>({
  columns,
  remoteFetchFn: async () => {
    const response = await getMarketplaces();
    return createPaginatedResponse({
      code: response.code,
      msg: response.msg,
      data: response.data || [],
      total: response.data?.length || 0,
      page: 1,
      page_size: 100,
    });
  },
});

// 测试连接
const handleTest = async (marketplace: Marketplace) => {
  testingIds.value.add(marketplace.id);
  try {
    const response = await testMarketplace(marketplace.id);
    if (response.data) {
      testResults.value.set(marketplace.id, response.data);
      if (response.data.success) {
        notifySuccess(`市场连接正常，延迟 ${response.data.latency_ms}ms`);
      } else {
        notifyError(`连接失败: ${response.data.message}`);
      }
    }
  } catch (error: any) {
    console.error("测试市场连接失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "测试失败";
    notifyError(errorMessage);
  } finally {
    testingIds.value.delete(marketplace.id);
  }
};

// 检查更新
const handleCheckUpdates = async (marketplace: Marketplace) => {
  try {
    const response = await checkUpdates(marketplace.id);
    if (response.data) {
      const updates = response.data.filter(u => u.has_update);
      if (updates.length === 0) {
        notifySuccess("所有插件已是最新版本");
      } else {
        notifySuccess(`发现 ${updates.length} 个插件有更新`);
      }
    }
  } catch (error: any) {
    console.error("检查更新失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "检查更新失败";
    notifyError(errorMessage);
  }
};

// 浏览远程插件
const handleBrowse = (marketplace: Marketplace) => {
  router.push(`/admin/marketplaces/${marketplace.id}/browse`);
};

// 编辑
const handleEdit = (marketplace: Marketplace) => {
  router.push(`/admin/marketplaces/${marketplace.id}/edit`);
};

// 删除
const handleDelete = async (marketplace: Marketplace) => {
  if (!(await confirmAction(`确定要删除市场 "${marketplace.name}" 吗？删除后不可恢复。`))) return;

  try {
    await deleteMarketplace(marketplace.id);
    notifySuccess("市场已删除");
    dataTable.refresh();
  } catch (error: any) {
    console.error("删除市场失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "删除失败";
    notifyError(errorMessage);
  }
};

// 添加市场
const handleCreate = () => {
  router.push("/admin/marketplaces/create");
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="marketplace-list-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold">插件市场</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理插件市场配置，浏览和同步远程插件。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" data-testid="refresh-btn" @click="dataTable.refresh()">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button data-testid="create-btn" @click="handleCreate">
          <Plus class="mr-1 h-4 w-4" />
          添加市场
        </Button>
      </div>
    </div>

    <!-- 数据表格区 -->
    <div class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">市场列表</div>
            <div class="text-muted-foreground mt-1 text-xs">管理已配置的插件市场</div>
          </div>
        </div>
      </div>

      <div class="flex min-h-0 flex-1 flex-col px-5 pt-4">
        <DataTable data-testid="marketplace-table" :data-table="dataTable" :fixed-layout="true" />
      </div>
    </div>
  </div>
</template>
