<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, Save, RefreshCw } from "lucide-vue-next";
import { Button, Card, Badge, Input, Textarea } from "@/components";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import { getPluginConfig, updatePluginConfig } from "@/ai/api/plugin";
import type { PluginConfigResponse } from "@/ai/api/plugin";

const route = useRoute();
const router = useRouter();
const pluginId = route.params.pluginId as string;

const loading = ref(true);
const saving = ref(false);
const config = ref<PluginConfigResponse | null>(null);

// 编辑模式的运行时配置（JSON 字符串）
const runtimeConfigJson = ref("");

// 解析后的运行时配置
const parsedRuntimeConfig = computed(() => {
  try {
    return JSON.parse(runtimeConfigJson.value || "{}");
  } catch {
    return null;
  }
});

// JSON 格式是否有效
const isJsonValid = computed(() => {
  try {
    JSON.parse(runtimeConfigJson.value || "{}");
    return true;
  } catch {
    return false;
  }
});

// 是否有修改
const hasChanges = computed(() => {
  if (!config.value) return false;
  try {
    const original = JSON.stringify(config.value.runtime_config || {}, null, 2);
    return runtimeConfigJson.value !== original;
  } catch {
    return false;
  }
});

const loadConfig = async () => {
  loading.value = true;
  try {
    const response = await getPluginConfig(pluginId);
    if (response.data) {
      config.value = response.data;
      // 初始化编辑器内容
      runtimeConfigJson.value = JSON.stringify(response.data.runtime_config || {}, null, 2);
    }
  } catch (error: any) {
    console.error("加载插件配置失败:", error);
    notifyError(error?.response?.data?.msg || "加载插件配置失败");
  } finally {
    loading.value = false;
  }
};

const handleBack = () => {
  router.push("/ai/plugins");
};

const handleReset = () => {
  if (config.value) {
    runtimeConfigJson.value = JSON.stringify(config.value.runtime_config || {}, null, 2);
  }
};

const handleSave = async () => {
  if (!isJsonValid.value) {
    notifyError("JSON 格式无效，请检查语法");
    return;
  }

  if (!hasChanges.value) {
    notifyError("未修改任何内容");
    return;
  }

  saving.value = true;
  try {
    const response = await updatePluginConfig(pluginId, {
      runtime_config: parsedRuntimeConfig.value,
    });
    if (response.data) {
      config.value = response.data;
      runtimeConfigJson.value = JSON.stringify(response.data.runtime_config || {}, null, 2);
      notifySuccess("配置已保存");
    }
  } catch (error: any) {
    console.error("保存配置失败:", error);
    notifyError(error?.response?.data?.msg || "保存配置失败");
  } finally {
    saving.value = false;
  }
};

const formatJson = () => {
  try {
    const parsed = JSON.parse(runtimeConfigJson.value || "{}");
    runtimeConfigJson.value = JSON.stringify(parsed, null, 2);
  } catch {
    // 格式化失败，保持原样
  }
};

onMounted(() => {
  loadConfig();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-config-page">
    <!-- 页面标题区 -->
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="handleBack">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回列表
      </Button>
      <h2 class="text-xl font-semibold">插件配置</h2>
      <Badge v-if="config" variant="outline">{{ config.plugin_id }}</Badge>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">加载中...</div>
    </div>

    <!-- 配置内容 -->
    <template v-else-if="config">
      <!-- 插件能力配置（只读） -->
      <Card class="p-5">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">插件能力配置</h3>
            <Badge variant="secondary">只读</Badge>
          </div>
          <div class="min-h-0 overflow-auto rounded-md bg-muted/50 p-4">
            <pre class="text-xs font-mono whitespace-pre-wrap break-all">{{
              JSON.stringify(config.plugin_config, null, 2)
            }}</pre>
          </div>
        </div>
      </Card>

      <!-- 运行时配置（可编辑） -->
      <Card class="flex min-h-0 flex-1 flex-col overflow-hidden p-5">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">运行时配置</h3>
            <div class="flex gap-2">
              <Button variant="outline" size="sm" @click="formatJson">
                格式化
              </Button>
              <Button variant="outline" size="sm" @click="handleReset" :disabled="!hasChanges">
                重置
              </Button>
            </div>
          </div>

          <!-- JSON 编辑器 -->
          <div class="space-y-2">
            <textarea
              v-model="runtimeConfigJson"
              class="min-h-[300px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              :class="{ 'border-destructive': !isJsonValid }"
              placeholder="{}"
              spellcheck="false"
            />
            <div v-if="!isJsonValid" class="text-destructive text-sm">
              JSON 格式无效，请检查语法
            </div>
          </div>
        </div>
      </Card>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-2">
        <Button variant="outline" @click="handleBack">取消</Button>
        <Button
          :disabled="!hasChanges || !isJsonValid || saving"
          @click="handleSave"
        >
          <Save v-if="!saving" class="mr-1 h-4 w-4" />
          <RefreshCw v-else class="mr-1 h-4 w-4 animate-spin" />
          {{ saving ? "保存中..." : "保存配置" }}
        </Button>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-else class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">插件配置不存在</div>
    </div>
  </div>
</template>
