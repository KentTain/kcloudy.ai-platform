<script setup lang="ts">
/**
 * 插件管理页面
 *
 * 卡片式布局，类似应用商店设计。类型筛选为按钮组，无限滚动加载。
 */
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { Badge, Button, Input, Card } from "@/components";
import { Tabs, TabsList, TabsTrigger } from "@/components";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
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
  Cpu,
  Wrench,
  Bot,
  LayoutGrid,
} from "lucide-vue-next";
import { useRouter } from "vue-router";

const router = useRouter();

// ========== 搜索筛选 ==========

const searchKeyword = ref("");
const activeType = ref("all");

// ========== 类型按钮组配置 ==========

const typeOptions = [
  { value: "all", label: "所有", icon: LayoutGrid },
  { value: "model", label: "模型", icon: Cpu },
  { value: "tool", label: "工具", icon: Wrench },
  { value: "agent", label: "代理", icon: Bot },
] as const;

// ========== 状态管理 ==========

const plugins = ref<AvailablePlugin[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = 10;
const totalCount = ref(0);
const hasMore = computed(() => plugins.value.length < totalCount.value);

const installingPlugins = ref<Set<string>>(new Set());
const operatingPlugins = ref<Set<string>>(new Set());

// 统计数据
const statistics = ref({
  total: 0,
  installed: 0,
  recommended: 0,
});

// 类型文本映射
const typeTextMap: Record<string, string> = {
  model: "模型",
  tool: "工具",
  agent: "代理",
  unknown: "未知",
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

// 状态颜色映射
const statusColorMap: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  INSTALLED: "default",
  ACTIVE: "default",
  INACTIVE: "outline",
  PENDING: "outline",
  INSTALLING: "outline",
  FAILED: "destructive",
};

// ========== 数据加载 ==========

let abortController: AbortController | null = null;

async function fetchPlugins(append = false) {
  if (!append) {
    abortController?.abort();
    abortController = new AbortController();
  }
  loading.value = true;

  try {
    const response = await getAvailablePlugins({
      page: currentPage.value,
      page_size: pageSize,
      keyword: searchKeyword.value || undefined,
      type: activeType.value === "all" ? undefined : activeType.value,
    });

    if (response.code === 200) {
      const items = response.data || [];
      if (append) {
        plugins.value = [...plugins.value, ...items];
      } else {
        plugins.value = items;
      }
      totalCount.value = response.total || 0;

      // 更新统计（仅首页数据）
      if (currentPage.value === 1) {
        statistics.value = {
          total: response.total || 0,
          installed: items.filter((p) => p.is_installed).length,
          recommended: items.filter((p) => p.is_recommended).length,
        };
      }
    }
  } catch {
    // 请求被取消或网络错误，静默处理
  } finally {
    loading.value = false;
  }
}

function reload() {
  currentPage.value = 1;
  plugins.value = [];
  fetchPlugins(false);
}

function loadMore() {
  if (!hasMore.value || loading.value) return;
  currentPage.value += 1;
  fetchPlugins(true);
}

// ========== 无限滚动 ==========

const scrollContainer = ref<HTMLElement | null>(null);
const sentinelRef = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

function setupObserver() {
  if (observer) observer.disconnect();
  if (!sentinelRef.value) return;

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value && !loading.value) {
        loadMore();
      }
    },
    { root: scrollContainer.value, rootMargin: "200px", threshold: 0 },
  );
  observer.observe(sentinelRef.value);
}

onMounted(() => {
  fetchPlugins();
  nextTick(() => setupObserver());
});

onUnmounted(() => {
  observer?.disconnect();
  abortController?.abort();
});

// 筛选变更时重新加载
watch(activeType, () => reload());

// ========== 搜索 ==========

let searchTimer: ReturnType<typeof setTimeout> | null = null;

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => reload(), 300);
}

function handleSearch() {
  reload();
}

// ========== 操作处理 ==========

function handleConfig(plugin: AvailablePlugin) {
  router.push(`/ai/plugins/${encodeURIComponent(plugin.plugin_id)}/config`);
}

async function handleInstall(plugin: AvailablePlugin) {
  installingPlugins.value.add(plugin.plugin_id);

  try {
    const response = await createPluginInstallation({
      plugin_id: plugin.plugin_id,
      auto_start: true,
    });

    if (response.code === 200) {
      notifySuccess(`插件 "${plugin.name}" 安装任务已创建`);
      reload();
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
}

async function handleStart(plugin: AvailablePlugin) {
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
      reload();
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
}

async function handleStop(plugin: AvailablePlugin) {
  operatingPlugins.value.add(plugin.plugin_id);

  try {
    const response = await stopPlugin(plugin.plugin_id);
    if (response.code === 200) {
      notifySuccess(`插件 "${plugin.name}" 已停止`);
      reload();
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
}

// ========== 辅助函数 ==========

function getPluginDisplayName(plugin: AvailablePlugin) {
  return plugin.name || plugin.plugin_id.split("/").pop();
}

function getPluginStatusText(plugin: AvailablePlugin) {
  if (!plugin.is_installed) return "未安装";
  return statusTextMap[plugin.installation_status || "INSTALLED"] || plugin.installation_status;
}

function getPluginStatusVariant(plugin: AvailablePlugin): "default" | "secondary" | "destructive" | "outline" {
  if (!plugin.is_installed) return "secondary";
  return statusColorMap[plugin.installation_status || "INSTALLED"] || "outline";
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-manage-page">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-3 gap-4">
      <Card class="p-4">
        <div class="flex items-center gap-4">
          <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
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
          <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/10">
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
          <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-500/10">
            <Sparkles class="h-6 w-6 text-amber-500" />
          </div>
          <div>
            <div class="text-2xl font-bold">{{ statistics.recommended }}</div>
            <div class="text-sm text-muted-foreground">推荐插件</div>
          </div>
        </div>
      </Card>
    </div>

    <!-- 筛选栏 + 卡片列表 -->
    <div class="ring-foreground/10 bg-card text-card-foreground rounded-xl text-sm ring-1 shadow-sm flex min-h-0 flex-1 flex-col overflow-hidden">
      <!-- 筛选栏 -->
      <div class="shrink-0 border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-4">
            <!-- 类型按钮组 -->
            <Tabs v-model="activeType">
              <TabsList>
                <TabsTrigger
                  v-for="opt in typeOptions"
                  :key="opt.value"
                  :value="opt.value"
                  :data-testid="`type-tab-${opt.value}`"
                >
                  <component :is="opt.icon" class="h-3.5 w-3.5" />
                  {{ opt.label }}
                </TabsTrigger>
              </TabsList>
            </Tabs>

            <!-- 搜索框 -->
            <div class="relative">
              <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                v-model="searchKeyword"
                placeholder="搜索插件..."
                data-testid="search-input"
                class="w-56 pl-8"
                @input="handleSearchInput"
                @keyup.enter="handleSearch"
              />
            </div>
          </div>

          <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" @click="reload">
              <RefreshCw class="mr-1 h-4 w-4" />
              刷新
            </Button>
          </div>
        </div>
      </div>

      <!-- 卡片列表区域 -->
      <ScrollArea class="flex-1" ref="scrollContainer" @scroll="setupObserver">
        <div class="grid grid-cols-2 gap-4 p-5 xl:grid-cols-3 2xl:grid-cols-4">
          <!-- 插件卡片 -->
          <div
            v-for="plugin in plugins"
            :key="plugin.plugin_id"
            class="group relative rounded-lg border bg-background p-4 transition-shadow hover:shadow-md"
            data-testid="plugin-card"
          >
            <!-- 卡片内容 -->
            <div class="flex items-start gap-3">
              <!-- 图标 -->
              <div v-if="plugin.icon" class="shrink-0">
                <img
                  :src="plugin.icon"
                  class="h-10 w-10 rounded-lg object-cover"
                  :alt="plugin.name"
                />
              </div>
              <div
                v-else
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted"
              >
                <Package class="h-5 w-5 text-muted-foreground" />
              </div>

              <!-- 名称和描述 -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="truncate font-medium">{{ getPluginDisplayName(plugin) }}</span>
                  <Badge v-if="plugin.is_recommended" variant="outline" class="shrink-0 text-xs">
                    推荐
                  </Badge>
                </div>
                <div class="mt-1 flex items-center gap-2">
                  <Badge variant="outline" class="text-xs">
                    {{ typeTextMap[plugin.plugin_type] || plugin.plugin_type }}
                  </Badge>
                  <Badge :variant="getPluginStatusVariant(plugin)" class="text-xs">
                    {{ getPluginStatusText(plugin) }}
                  </Badge>
                </div>
                <p
                  v-if="plugin.description"
                  class="mt-2 line-clamp-2 text-xs text-muted-foreground"
                >
                  {{ plugin.description }}
                </p>
              </div>
            </div>

            <!-- 悬停操作按钮：左下角 -->
            <div
              class="absolute bottom-3 left-3 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100"
            >
              <!-- 已安装插件的操作 -->
              <template v-if="plugin.is_installed">
                <Button
                  variant="ghost"
                  size="sm"
                  class="h-7 px-2 text-xs"
                  data-testid="config-btn"
                  @click="handleConfig(plugin)"
                >
                  <Settings class="mr-1 h-3 w-3" />
                  配置
                </Button>
                <Button
                  v-if="plugin.installation_status === 'ACTIVE'"
                  variant="ghost"
                  size="sm"
                  class="h-7 px-2 text-xs"
                  :disabled="operatingPlugins.has(plugin.plugin_id)"
                  data-testid="stop-btn"
                  @click="handleStop(plugin)"
                >
                  <template v-if="operatingPlugins.has(plugin.plugin_id)">
                    <Loader2 class="mr-1 h-3 w-3 animate-spin" />
                    停止中
                  </template>
                  <template v-else>
                    <Square class="mr-1 h-3 w-3" />
                    停止
                  </template>
                </Button>
                <Button
                  v-else-if="plugin.installation_status === 'INACTIVE'"
                  variant="ghost"
                  size="sm"
                  class="h-7 px-2 text-xs"
                  :disabled="operatingPlugins.has(plugin.plugin_id)"
                  data-testid="start-btn"
                  @click="handleStart(plugin)"
                >
                  <template v-if="operatingPlugins.has(plugin.plugin_id)">
                    <Loader2 class="mr-1 h-3 w-3 animate-spin" />
                    启动中
                  </template>
                  <template v-else>
                    <Play class="mr-1 h-3 w-3" />
                    启动
                  </template>
                </Button>
              </template>

              <!-- 未安装插件的操作 -->
              <Button
                v-else
                variant="default"
                size="sm"
                class="h-7 px-2 text-xs"
                :disabled="installingPlugins.has(plugin.plugin_id)"
                data-testid="install-btn"
                @click="handleInstall(plugin)"
              >
                <template v-if="installingPlugins.has(plugin.plugin_id)">
                  <Loader2 class="mr-1 h-3 w-3 animate-spin" />
                  安装中
                </template>
                <template v-else>
                  <Download class="mr-1 h-3 w-3" />
                  安装
                </template>
              </Button>
            </div>
          </div>

          <!-- 加载骨架屏 -->
          <template v-if="loading && plugins.length === 0">
            <div v-for="i in 6" :key="`skeleton-${i}`" class="rounded-lg border bg-background p-4">
              <div class="flex items-start gap-3">
                <Skeleton class="h-10 w-10 shrink-0 rounded-lg" />
                <div class="flex-1 space-y-2">
                  <Skeleton class="h-4 w-24" />
                  <Skeleton class="h-3 w-16" />
                  <Skeleton class="h-3 w-full" />
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- 空状态 -->
        <div
          v-if="!loading && plugins.length === 0"
          class="flex flex-col items-center justify-center py-20 text-muted-foreground"
        >
          <Package class="mb-3 h-12 w-12" />
          <span>暂无插件</span>
        </div>

        <!-- 加载更多指示器 -->
        <div v-if="loading && plugins.length > 0" class="flex items-center justify-center py-4">
          <Loader2 class="mr-2 h-4 w-4 animate-spin text-muted-foreground" />
          <span class="text-sm text-muted-foreground">加载更多...</span>
        </div>

        <!-- 无限滚动哨兵 -->
        <div ref="sentinelRef" class="h-1" />

        <!-- 已全部加载提示 -->
        <div
          v-if="!hasMore && plugins.length > 0 && !loading"
          class="pb-4 text-center text-xs text-muted-foreground"
        >
          已加载全部 {{ plugins.length }} 个插件
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
