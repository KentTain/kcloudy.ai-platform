<script setup lang="ts">
/**
 * 模型配置页面
 *
 * 上下布局：上方统计卡片+默认模型配置，下方二级树表格。
 */
import { ref, computed, onMounted } from "vue";
import { Button, Input } from "@/components";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import { Search, RefreshCw, Loader2 } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { getModelConfigOverview } from "@/ai/api/modelConfig";
import type {
  ModelConfigOverviewResponse,
  PluginWithModels,
  ModelConfigItem,
  DefaultModelItem,
} from "@/ai/types/modelConfig";
import ModelConfigStats from "@/ai/components/model-config/ModelConfigStats.vue";
import DefaultModelDisplay from "@/ai/components/model-config/DefaultModelDisplay.vue";
import ModelConfigTable from "@/ai/components/model-config/ModelConfigTable.vue";
import ConfigureModelsDialog from "@/ai/components/model-config/ConfigureModelsDialog.vue";
import SetDefaultModelDialog from "@/ai/components/model-config/SetDefaultModelDialog.vue";

const router = useRouter();

// ========== 数据 ==========

const loading = ref(false);
const overview = ref<ModelConfigOverviewResponse | null>(null);

// ========== 筛选 ==========

const searchKeyword = ref("");
const statusFilter = ref<string>("__all__");

let searchTimer: ReturnType<typeof setTimeout> | null = null;
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    // 筛选由 computed 处理，无需额外操作
  }, 300);
}

const filteredPlugins = computed(() => {
  if (!overview.value) return [];
  let result = overview.value.plugins;

  // 状态筛选
  if (statusFilter.value !== "__all__") {
    result = result.filter((p) => p.status === statusFilter.value);
  }

  // 关键词搜索：匹配插件编码/名称 或 模型编码/名称
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase();
    result = result.filter((p) => {
      const pluginMatch =
        p.plugin_id.toLowerCase().includes(kw) || p.plugin_name.toLowerCase().includes(kw);
      const modelMatch = p.models.some(
        (m) =>
          m.model_name.toLowerCase().includes(kw) ||
          (m.model_label && m.model_label.toLowerCase().includes(kw)),
      );
      return pluginMatch || modelMatch;
    });
  }

  return result;
});

// ========== 数据加载 ==========

async function fetchOverview() {
  loading.value = true;
  try {
    overview.value = await getModelConfigOverview();
  } catch {
    notifyError("获取模型配置数据失败");
  } finally {
    loading.value = false;
  }
}

// ========== 配置模型弹窗 ==========

const configureDialogOpen = ref(false);
const configurePlugin = ref<PluginWithModels | null>(null);

function handleConfigureModels(plugin: PluginWithModels) {
  configurePlugin.value = plugin;
  configureDialogOpen.value = true;
}

// ========== 设置默认模型弹窗 ==========

const setDefaultDialogOpen = ref(false);
const setDefaultMode = ref<"llm" | "embedding-rerank">("llm");
const setDefaultModel = ref<ModelConfigItem | null>(null);
const setDefaultPlugin = ref<PluginWithModels | null>(null);

function handleSetDefault(model: ModelConfigItem, plugin: PluginWithModels) {
  setDefaultModel.value = model;
  setDefaultPlugin.value = plugin;

  if (model.model_type === "llm") {
    setDefaultMode.value = "llm";
  } else {
    setDefaultMode.value = "embedding-rerank";
  }

  setDefaultDialogOpen.value = true;
}

function getCurrentDefault(): DefaultModelItem | undefined {
  if (!overview.value) return undefined;
  if (setDefaultMode.value === "llm") {
    return overview.value.default_models.find((d) => d.model_type === "llm");
  }
  // embedding-rerank 模式，返回第一个匹配的
  return overview.value.default_models.find(
    (d) => d.model_type === "text-embedding" || d.model_type === "rerank",
  );
}

// ========== 查看插件详情 ==========

function handleViewDetail(pluginId: string) {
  router.push({
    name: "AIPluginConfig",
    params: { pluginId },
  });
}

// ========== 初始化 ==========

onMounted(() => {
  fetchOverview();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="model-config-page">
    <!-- 上方：统计卡片 + 默认模型配置 -->
    <div class="space-y-4">
      <ModelConfigStats
        :total-plugins="overview?.total_plugins ?? 0"
        :configured-plugins="overview?.configured_plugins ?? 0"
        :total-models="overview?.total_models ?? 0"
      />
      <DefaultModelDisplay :default-models="overview?.default_models ?? []" />
    </div>

    <!-- 下方：筛选栏 + 树表格 -->
    <div
      class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden"
    >
      <!-- 筛选栏 -->
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-4">
            <!-- 状态筛选 -->
            <div class="flex items-center gap-2">
              <select
                v-model="statusFilter"
                class="h-9 rounded-md border border-input bg-background px-3 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="__all__">全部状态</option>
                <option value="active">已启动</option>
                <option value="inactive">已停止</option>
              </select>
            </div>
            <!-- 搜索框 -->
            <div class="relative">
              <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                v-model="searchKeyword"
                placeholder="搜索插件或模型..."
                class="w-64 pl-9"
                @input="onSearchInput"
              />
            </div>
          </div>
          <Button variant="outline" size="sm" :disabled="loading" @click="fetchOverview">
            <RefreshCw class="mr-1 h-4 w-4" :class="{ 'animate-spin': loading }" />
            刷新
          </Button>
        </div>
      </div>

      <!-- 数据表格 -->
      <div class="flex min-h-0 flex-1 flex-col overflow-auto px-5 pt-4">
        <div v-if="loading" class="flex items-center justify-center py-12">
          <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
        <ModelConfigTable
          v-else
          :plugins="filteredPlugins"
          :default-models="overview?.default_models ?? []"
          @configure-models="handleConfigureModels"
          @set-default="handleSetDefault"
          @view-detail="handleViewDetail"
        />
      </div>
    </div>

    <!-- 配置模型弹窗 -->
    <ConfigureModelsDialog
      v-model:open="configureDialogOpen"
      :plugin-id="configurePlugin?.plugin_id ?? ''"
      :plugin-name="configurePlugin?.plugin_name ?? ''"
      @saved="fetchOverview"
    />

    <!-- 设置默认模型弹窗 -->
    <SetDefaultModelDialog
      v-model:open="setDefaultDialogOpen"
      :model-type="setDefaultMode"
      :current-default="getCurrentDefault()"
      :plugin-id="setDefaultPlugin?.plugin_id"
      @saved="fetchOverview"
    />
  </div>
</template>
