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
  RefreshCw,
} from "@lucide/vue";
import type { ColumnDef } from "@tanstack/vue-table";
import { h, ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Badge, Button, DataTable, Input, useDataTable } from "@/components";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import SkillCard from "@/ai/components/SkillCard.vue";
import SkillPreviewDialog from "@/ai/components/SkillPreviewDialog.vue";
import { notifyError, notifySuccess } from "@/framework/utils/feedback";
import { createPaginatedResponse } from "@/framework/api/types";
import {
  getMarketplace,
  getRemotePlugins,
  syncPlugins,
} from "@/tenant/api/marketplace";
import {
  syncSkillFromMarketplace,
  getInstalledSkills,
  type RemoteSkillInfo,
  type PluginDefinition,
} from "@/tenant/api/plugin";
import type { Marketplace, RemotePlugin } from "@/tenant/types/marketplace";

const route = useRoute();
const router = useRouter();

const marketplaceId = computed(() => route.params.id as string);

// ==================== 市场信息 ====================

const marketplace = ref<Marketplace | null>(null);
const loadingMarketplace = ref(false);

const supportedTypes = computed(() => marketplace.value?.supported_types || []);

const hasSkillTab = computed(() => supportedTypes.value.includes("skill"));
const hasPluginTab = computed(
  () =>
    supportedTypes.value.includes("tool") ||
    supportedTypes.value.includes("model") ||
    supportedTypes.value.includes("agent") ||
    supportedTypes.value.includes("mcp"),
);

const activeTab = ref<string>("");

// 默认选中第一个可用 Tab
watch(
  [hasSkillTab, hasPluginTab],
  ([skill, plugin]) => {
    if (!skill && !plugin) return;
    if (activeTab.value) return;
    activeTab.value = plugin ? "plugin" : "skill";
  },
  { immediate: true },
);

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

// 市场类型标签
const typeLabelMap: Record<string, string> = {
  dify: "Dify 市场",
  agentskills: "AgentSkills 市场",
  "modelscope-skill": "ModelScope Skill",
  "modelscope-mcp": "ModelScope MCP",
  "local-skill": "本地 Skill 目录",
  "local-plugin": "本地 Plugin 目录",
};

// ==================== Plugin Tab ====================

const pluginSearchForm = ref({ keyword: "", type: "" });
const selectedPluginIds = ref<Map<string, string>>(new Map());
const isPluginSyncing = ref(false);

function formatNumber(num?: number): string {
  if (!num) return "0";
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
}

function getTypeLabel(type: string): string {
  switch (type) {
    case "tool":
      return "工具";
    case "model":
      return "模型";
    case "agent":
      return "Agent";
    case "mcp":
      return "MCP";
    default:
      return type;
  }
}

const pluginColumns: ColumnDef<RemotePlugin>[] = [
  {
    id: "selection",
    header: () =>
      h("input", {
        type: "checkbox",
        class: "cursor-pointer",
        checked: selectedPluginIds.value.size > 0,
        onChange: (e: Event) => {
          const target = e.target as HTMLInputElement;
          if (!target.checked) {
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
          onClick: () => handleSyncSinglePlugin(plugin),
        },
        () => [h(Download, { class: "mr-1 h-3.5 w-3.5" }), "同步"],
      );
    },
  },
];

const pluginDataTable = useDataTable<RemotePlugin>({
  columns: pluginColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getRemotePlugins(marketplaceId.value, {
      page,
      page_size,
      keyword: pluginSearchForm.value.keyword || undefined,
      type: pluginSearchForm.value.type || undefined,
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

const handlePluginSearch = () => {
  pluginDataTable.refresh(true);
};

const handlePluginReset = () => {
  pluginSearchForm.value = { keyword: "", type: "" };
  selectedPluginIds.value.clear();
  pluginDataTable.refresh(true);
};

const handleSyncSinglePlugin = async (plugin: RemotePlugin) => {
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

const handleSyncSelectedPlugins = async () => {
  if (selectedPluginIds.value.size === 0) {
    notifyError("请先选择要同步的插件");
    return;
  }

  isPluginSyncing.value = true;
  try {
    const plugins = Array.from(selectedPluginIds.value.entries()).map(
      ([plugin_id, plugin_type]) => ({ plugin_id, plugin_type }),
    );
    const response = await syncPlugins({
      marketplace_id: marketplaceId.value,
      plugins,
    });
    if (response.data) {
      const { success, failed, skipped } = response.data;
      notifySuccess(
        `同步完成: 成功 ${success.length} 个，跳过 ${skipped.length} 个，失败 ${failed.length} 个`,
      );
      selectedPluginIds.value.clear();
    }
  } catch (error: any) {
    console.error("批量同步插件失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "同步失败";
    notifyError(errorMessage);
  } finally {
    isPluginSyncing.value = false;
  }
};

// ==================== Skill Tab ====================

const skillSearchKeyword = ref("");
const skillTypeFilter = ref<"all" | "knowledge" | "script">("all");
const skillLoading = ref(false);
const skillSyncing = ref(false);
const remoteSkills = ref<RemoteSkillInfo[]>([]);
const installedSkills = ref<PluginDefinition[]>([]);
const previewSkillId = ref<string | null>(null);
const previewOpen = ref(false);

const filteredSkills = computed(() => {
  let skills = remoteSkills.value;

  if (skillTypeFilter.value !== "all") {
    skills = skills.filter((s) => s.skill_type === skillTypeFilter.value);
  }

  if (skillSearchKeyword.value) {
    const keyword = skillSearchKeyword.value.toLowerCase();
    skills = skills.filter(
      (s) =>
        s.name.toLowerCase().includes(keyword) ||
        s.description?.toLowerCase().includes(keyword) ||
        s.tags.some((t) => t.toLowerCase().includes(keyword)),
    );
  }

  return skills;
});

const loadRemoteSkills = async () => {
  skillLoading.value = true;
  try {
    const res = await getRemotePlugins(marketplaceId.value, {
      keyword: skillSearchKeyword.value || undefined,
      type: "skill",
    });
    if (res.code === 200 && res.data) {
      remoteSkills.value = res.data as unknown as RemoteSkillInfo[];
    } else {
      notifyError(res.msg || "加载 Skill 列表失败");
    }
  } catch (error) {
    notifyError("加载 Skill 列表失败");
  } finally {
    skillLoading.value = false;
  }
};

const loadInstalledSkills = async () => {
  try {
    const res = await getInstalledSkills();
    if (res.code === 200 && res.data) {
      installedSkills.value = res.data;
    }
  } catch (error) {
    console.error("加载已安装 Skill 失败:", error);
  }
};

const isSkillInstalled = (skillId: string) => {
  return installedSkills.value.some((s) => s.plugin_id === skillId);
};

const handleInstallSkill = async (skill: RemoteSkillInfo) => {
  skillSyncing.value = true;
  try {
    const res = await syncSkillFromMarketplace(marketplaceId.value, skill.plugin_id);
    if (res.code === 200) {
      notifySuccess("Skill 安装成功");
      await loadInstalledSkills();
    } else {
      notifyError(res.msg || "安装失败");
    }
  } catch (error) {
    notifyError("安装失败");
  } finally {
    skillSyncing.value = false;
  }
};

const handlePreviewSkill = (skill: RemoteSkillInfo) => {
  previewSkillId.value = skill.plugin_id;
  previewOpen.value = true;
};

const handleSkillSearch = () => {
  loadRemoteSkills();
};

// ==================== 通用 ====================

const handleBack = () => {
  router.push("/admin/marketplaces");
};

onMounted(() => {
  loadMarketplace();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="marketplace-browse-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" data-testid="back-btn" @click="handleBack">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold">
            {{ marketplace?.name || "市场浏览" }}
          </h2>
          <p class="text-muted-foreground mt-1 text-sm">
            浏览市场中的插件并同步到本地
          </p>
        </div>
      </div>
    </div>

    <!-- 市场信息卡片 -->
    <div v-if="marketplace" class="grid gap-4 md:grid-cols-3">
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center gap-3">
          <Package class="h-8 w-8 opacity-20 text-blue-500" />
          <div>
            <p class="text-sm text-muted-foreground">市场类型</p>
            <p class="font-medium">{{ typeLabelMap[marketplace.type] || marketplace.type }}</p>
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
          <CheckCircle
            class="h-8 w-8 opacity-20"
            :class="marketplace.is_enabled ? 'text-green-500' : 'text-gray-500'"
          />
          <div>
            <p class="text-sm text-muted-foreground">状态</p>
            <Badge :variant="marketplace.is_enabled ? 'default' : 'secondary'">
              {{ marketplace.is_enabled ? "已启用" : "已禁用" }}
            </Badge>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 切换（仅当同时有 Plugin 和 Skill 时显示） -->
    <Tabs v-if="hasSkillTab && hasPluginTab" v-model="activeTab">
      <TabsList>
        <TabsTrigger value="plugin">插件</TabsTrigger>
        <TabsTrigger value="skill">Skill</TabsTrigger>
      </TabsList>
    </Tabs>

    <!-- ==================== Plugin Tab ==================== -->
    <template v-if="activeTab === 'plugin' && hasPluginTab">
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          :disabled="selectedPluginIds.size === 0 || isPluginSyncing"
          data-testid="sync-selected-btn"
          @click="handleSyncSelectedPlugins"
        >
          <Loader2 v-if="isPluginSyncing" class="mr-1 h-4 w-4 animate-spin" />
          <CheckCircle v-else class="mr-1 h-4 w-4" />
          {{ isPluginSyncing ? "同步中..." : `同步选中 (${selectedPluginIds.size})` }}
        </Button>
      </div>

      <div
        class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden"
      >
        <div class="shrink-0 border-b px-5 py-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="font-medium">远程插件列表</div>
              <div class="text-muted-foreground mt-1 text-xs">选择插件同步到本地插件定义</div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <Input
                v-model="pluginSearchForm.keyword"
                class="w-56"
                placeholder="搜索插件名称或 ID"
                data-testid="search-keyword-input"
                @keydown.enter="handlePluginSearch"
              />
              <Select v-model="pluginSearchForm.type">
                <SelectTrigger class="w-[120px]" data-testid="type-select">
                  <SelectValue placeholder="插件类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部类型</SelectItem>
                  <SelectItem value="tool">工具</SelectItem>
                  <SelectItem value="model">模型</SelectItem>
                  <SelectItem value="agent">Agent</SelectItem>
                  <SelectItem value="mcp">MCP</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" data-testid="search-btn" @click="handlePluginSearch">
                <Search class="mr-1 h-4 w-4" />
                搜索
              </Button>
              <Button variant="outline" data-testid="reset-btn" @click="handlePluginReset">
                <RotateCcw class="mr-1 h-4 w-4" />
                重置
              </Button>
            </div>
          </div>
        </div>

        <div class="flex min-h-0 flex-1 flex-col px-5 pt-4">
          <DataTable data-testid="remote-plugin-table" :data-table="pluginDataTable" :fixed-layout="true" />
        </div>
      </div>
    </template>

    <!-- ==================== Skill Tab ==================== -->
    <template v-if="activeTab === 'skill' && hasSkillTab">
      <!-- 搜索和筛选 -->
      <div class="flex items-center gap-4">
        <div class="relative max-w-md flex-1">
          <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            v-model="skillSearchKeyword"
            placeholder="搜索 Skill..."
            class="pl-10"
            @keydown.enter="handleSkillSearch"
          />
        </div>

        <Tabs v-model="skillTypeFilter" @update:model-value="handleSkillSearch">
          <TabsList>
            <TabsTrigger value="all">全部</TabsTrigger>
            <TabsTrigger value="knowledge">知识文档</TabsTrigger>
            <TabsTrigger value="script">简单脚本</TabsTrigger>
          </TabsList>
        </Tabs>

        <Button variant="outline" :disabled="skillLoading" @click="loadRemoteSkills">
          <RefreshCw v-if="skillLoading" class="mr-1 h-4 w-4 animate-spin" />
          <RefreshCw v-else class="mr-1 h-4 w-4" />
          刷新
        </Button>
      </div>

      <!-- Skill 列表 -->
      <div v-if="skillLoading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 6" :key="i" class="h-48 animate-pulse rounded-lg bg-muted" />
      </div>

      <div v-else-if="filteredSkills.length > 0" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <SkillCard
          v-for="skill in filteredSkills"
          :key="skill.plugin_id"
          :skill="skill"
          :is-installed="isSkillInstalled(skill.plugin_id)"
          @install="handleInstallSkill"
          @preview="handlePreviewSkill"
        />
      </div>

      <div v-else class="py-12 text-center text-muted-foreground">
        <Loader2 v-if="skillSyncing" class="mx-auto mb-2 h-8 w-8 animate-spin" />
        暂无 Skill 数据
      </div>

      <!-- 预览对话框 -->
      <SkillPreviewDialog v-model:open="previewOpen" :skill-id="previewSkillId" />
    </template>
  </div>
</template>
