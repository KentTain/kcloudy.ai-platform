<script setup lang="ts">
import { Check, ChevronRight, FolderSearch, Loader2, AlertCircle, CheckCircle, SkipForward } from '@lucide/vue';
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Button, Card, Input, Checkbox } from '@/components';
import { notifyError } from '@/framework/utils/feedback';
import {
  scanDirectoryPreview,
  scanDirectoryForPlugins,
} from '@/tenant/api/plugin';
import type { ScannedPluginPreview, ScannedPluginResult } from '@/tenant/api/plugin';

const router = useRouter();

// 步骤状态
const currentStep = ref(0);
const steps = [
  { title: '输入路径', description: '配置扫描目录' },
  { title: '预览选择', description: '选择要导入的插件' },
  { title: '导入结果', description: '查看导入状态' },
];

// 第一步：输入路径
const scanForm = ref({
  directory: '',
  recursive: true,
});
const isScanning = ref(false);

// 第二步：预览选择
const scannedPlugins = ref<ScannedPluginPreview[]>([]);
const selectedPluginIds = ref<Set<string>>(new Set());

// 第三步：导入结果
const importResults = ref<ScannedPluginResult[]>([]);
const isImporting = ref(false);

// 计算属性：可选择的插件（未存在且状态正常）
const selectablePlugins = computed(() =>
  scannedPlugins.value.filter((p) => !p.exists && p.status === 'ready')
);

// 计算属性：统计信息
const importStats = computed(() => {
  const success = importResults.value.filter((r) => r.status === 'success').length;
  const skipped = importResults.value.filter((r) => r.status === 'skipped').length;
  const failed = importResults.value.filter((r) => r.status === 'failed').length;
  return { success, skipped, failed, total: importResults.value.length };
});

// 第一步：扫描目录预览
const handleScan = async () => {
  if (!scanForm.value.directory.trim()) {
    notifyError('请输入服务器目录路径');
    return;
  }

  isScanning.value = true;
  selectedPluginIds.value.clear();
  scannedPlugins.value = [];

  try {
    const response = await scanDirectoryPreview({
      directory: scanForm.value.directory,
      recursive: scanForm.value.recursive,
    });

    if (response.data) {
      scannedPlugins.value = response.data;
      if (scannedPlugins.value.length === 0) {
        notifyError('未在指定目录中找到插件');
        return;
      }
      currentStep.value = 1;
    }
  } catch (error: any) {
    console.error('扫描目录失败:', error);
    const errorMessage = error?.response?.data?.msg || error?.message || '扫描失败';
    notifyError(errorMessage);
  } finally {
    isScanning.value = false;
  }
};

// 第二步：选择插件
const togglePlugin = (pluginId: string) => {
  if (selectedPluginIds.value.has(pluginId)) {
    selectedPluginIds.value.delete(pluginId);
  } else {
    selectedPluginIds.value.add(pluginId);
  }
};

const selectAllSelectable = () => {
  selectablePlugins.value.forEach((p) => selectedPluginIds.value.add(p.plugin_id));
};

const clearSelection = () => {
  selectedPluginIds.value.clear();
};

// 第二步：确认导入
const handleImport = async () => {
  if (selectedPluginIds.value.size === 0) {
    notifyError('请至少选择一个插件');
    return;
  }

  isImporting.value = true;
  importResults.value = [];

  try {
    const response = await scanDirectoryForPlugins({
      directory: scanForm.value.directory,
      recursive: scanForm.value.recursive,
      plugin_ids: Array.from(selectedPluginIds.value),
    });

    if (response.data) {
      importResults.value = response.data.results;
      currentStep.value = 2;
    }
  } catch (error: any) {
    console.error('导入插件失败:', error);
    const errorMessage = error?.response?.data?.msg || error?.message || '导入失败';
    notifyError(errorMessage);
  } finally {
    isImporting.value = false;
  }
};

// 第三步：返回或完成
const handleBack = () => {
  currentStep.value = 0;
  scannedPlugins.value = [];
  selectedPluginIds.value.clear();
  importResults.value = [];
};

const handleFinish = () => {
  router.push('/admin/plugin-definitions');
};

// 辅助函数：获取状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success':
      return CheckCircle;
    case 'skipped':
      return SkipForward;
    case 'failed':
      return AlertCircle;
    default:
      return AlertCircle;
  }
};

// 辅助函数：获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'success':
      return 'text-green-600';
    case 'skipped':
      return 'text-amber-600';
    case 'failed':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};

// 辅助函数：获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'success':
      return '成功';
    case 'skipped':
      return '跳过';
    case 'failed':
      return '失败';
    default:
      return '未知';
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-scan-page">
    <!-- 页面标题 -->
    <div>
      <h2 class="text-xl font-semibold">扫描目录</h2>
      <p class="text-muted-foreground mt-1 text-sm">
        从服务器目录扫描并导入插件定义
      </p>
    </div>

    <!-- 步骤指示器 -->
    <div class="flex items-center justify-center gap-2">
      <template v-for="(step, index) in steps" :key="index">
        <div
          class="flex items-center gap-2 rounded-full px-4 py-2 transition-colors"
          :class="[
            currentStep === index
              ? 'bg-primary text-primary-foreground'
              : currentStep > index
                ? 'bg-primary/10 text-primary'
                : 'bg-muted text-muted-foreground',
          ]"
        >
          <div
            class="flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold"
            :class="[
              currentStep === index
                ? 'bg-primary-foreground/20'
                : currentStep > index
                  ? 'bg-primary/20'
                  : 'bg-muted-foreground/20',
            ]"
          >
            <Check v-if="currentStep > index" class="h-4 w-4" />
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="text-sm font-medium">{{ step.title }}</div>
        </div>
        <ChevronRight
          v-if="index < steps.length - 1"
          class="text-muted-foreground h-4 w-4"
        />
      </template>
    </div>

    <!-- 步骤内容 -->
    <Card class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <!-- 第一步：输入路径 -->
      <div
        v-if="currentStep === 0"
        class="flex flex-1 flex-col items-center justify-center gap-6 p-8"
      >
        <div class="w-full max-w-lg space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">服务器目录路径</label>
            <Input
              v-model="scanForm.directory"
              placeholder="/path/to/plugins"
              data-testid="directory-input"
            />
            <p class="text-muted-foreground text-xs">
              输入服务器上存放插件包的目录路径
            </p>
          </div>

          <div class="flex items-center gap-2">
            <Checkbox
              :checked="scanForm.recursive"
              @update:checked="scanForm.recursive = $event"
              data-testid="recursive-checkbox"
            />
            <label class="text-sm">递归扫描子目录</label>
          </div>

          <Button
            class="w-full"
            :disabled="isScanning"
            data-testid="scan-btn"
            @click="handleScan"
          >
            <Loader2 v-if="isScanning" class="mr-2 h-4 w-4 animate-spin" />
            <FolderSearch v-else class="mr-2 h-4 w-4" />
            {{ isScanning ? '扫描中...' : '开始扫描' }}
          </Button>
        </div>
      </div>

      <!-- 第二步：预览选择 -->
      <div
        v-if="currentStep === 1"
        class="flex min-h-0 flex-1 flex-col overflow-hidden"
      >
        <div class="border-b px-5 py-4">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium">扫描结果</div>
              <div class="text-muted-foreground mt-1 text-xs">
                共扫描到 {{ scannedPlugins.length }} 个插件，已选择
                {{ selectedPluginIds.size }} 个
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Button variant="outline" size="sm" @click="selectAllSelectable">
                全选可选
              </Button>
              <Button variant="outline" size="sm" @click="clearSelection">
                清空选择
              </Button>
            </div>
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-auto p-5">
          <div class="space-y-2">
            <div
              v-for="plugin in scannedPlugins"
              :key="plugin.plugin_id"
              class="flex items-center justify-between rounded-lg border p-4 transition-colors"
              :class="[
                plugin.exists
                  ? 'cursor-not-allowed bg-muted/50 opacity-60'
                  : plugin.status === 'invalid'
                    ? 'cursor-not-allowed bg-red-50'
                    : selectedPluginIds.has(plugin.plugin_id)
                      ? 'border-primary bg-primary/5'
                      : 'cursor-pointer hover:bg-muted/50',
              ]"
              @click="
                !plugin.exists &&
                  plugin.status === 'ready' &&
                  togglePlugin(plugin.plugin_id)
              "
            >
              <div class="flex items-center gap-3">
                <Checkbox
                  :model-value="selectedPluginIds.has(plugin.plugin_id)"
                  :disabled="plugin.exists || plugin.status === 'invalid'"
                  @update:model-value="togglePlugin(plugin.plugin_id)"
                />
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-medium">{{ plugin.plugin_id }}</span>
                    <span class="text-muted-foreground text-xs">
                      v{{ plugin.version }}
                    </span>
                  </div>
                  <div class="text-muted-foreground text-xs">
                    {{ plugin.name }}
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <span
                  v-if="plugin.exists"
                  class="rounded bg-muted px-2 py-1 text-xs text-muted-foreground"
                >
                  已存在
                </span>
                <span
                  v-if="plugin.status === 'invalid'"
                  class="rounded bg-red-100 px-2 py-1 text-xs text-red-600"
                >
                  解析失败
                </span>
                <span
                  v-if="
                    !plugin.exists &&
                    plugin.status === 'ready' &&
                    selectedPluginIds.has(plugin.plugin_id)
                  "
                  class="rounded bg-primary/10 px-2 py-1 text-xs text-primary"
                >
                  待导入
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t px-5 py-4">
          <div class="flex items-center justify-between">
            <Button variant="outline" @click="currentStep = 0">
              上一步
            </Button>
            <Button
              :disabled="selectedPluginIds.size === 0 || isImporting"
              data-testid="import-btn"
              @click="handleImport"
            >
              <Loader2 v-if="isImporting" class="mr-2 h-4 w-4 animate-spin" />
              <Check v-else class="mr-2 h-4 w-4" />
              {{ isImporting ? '导入中...' : '确认导入' }}
            </Button>
          </div>
        </div>
      </div>

      <!-- 第三步：导入结果 -->
      <div
        v-if="currentStep === 2"
        class="flex min-h-0 flex-1 flex-col overflow-hidden"
      >
        <div class="border-b px-5 py-4">
          <div class="font-medium">导入结果</div>
          <div class="text-muted-foreground mt-1 text-xs">
            成功 {{ importStats.success }} 个，跳过 {{ importStats.skipped }} 个，失败
            {{ importStats.failed }} 个
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-auto p-5">
          <div class="space-y-2">
            <div
              v-for="result in importResults"
              :key="result.plugin_id"
              class="flex items-center justify-between rounded-lg border p-4"
            >
              <div class="flex items-center gap-3">
                <component
                  :is="getStatusIcon(result.status)"
                  class="h-5 w-5"
                  :class="getStatusColor(result.status)"
                />
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-medium">{{ result.plugin_id }}</span>
                    <span class="text-muted-foreground text-xs">
                      v{{ result.version }}
                    </span>
                  </div>
                  <div class="text-muted-foreground text-xs">
                    {{ result.message || getStatusText(result.status) }}
                  </div>
                </div>
              </div>

              <span
                class="rounded px-2 py-1 text-xs"
                :class="[
                  result.status === 'success'
                    ? 'bg-green-100 text-green-600'
                    : result.status === 'skipped'
                      ? 'bg-amber-100 text-amber-600'
                      : 'bg-red-100 text-red-600',
                ]"
              >
                {{ getStatusText(result.status) }}
              </span>
            </div>
          </div>
        </div>

        <div class="border-t px-5 py-4">
          <div class="flex items-center justify-between">
            <Button variant="outline" @click="handleBack">
              继续扫描
            </Button>
            <Button data-testid="finish-btn" @click="handleFinish">
              完成
            </Button>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
