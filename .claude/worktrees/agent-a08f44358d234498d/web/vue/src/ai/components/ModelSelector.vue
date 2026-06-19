<script setup lang="ts">
/**
 * 模型选择器组件
 *
 * 提供按提供商分组的模型选择功能。
 * 选择后自动同步到 conversationStore.currentModel。
 */
import { ref, computed, onMounted } from "vue";
import { Skeleton } from "@/components";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useConversationStore } from "@/ai/stores";
import { getModels, type ProviderItem } from "@/ai/api/model";
import type { ModelConfig } from "@/ai/types";

const conversationStore = useConversationStore();

// 模型列表数据
const providers = ref<ProviderItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// 当前选中的模型 ID（格式: provider/model）
const selectedModelId = computed({
  get: () => {
    const { provider, name } = conversationStore.currentModel;
    return `${provider}/${name}`;
  },
  set: (value: string) => {
    const [provider, name] = value.split("/");
    if (provider && name) {
      conversationStore.setModel({ provider, name } as ModelConfig);
    }
  },
});

// 获取选中模型的显示名称
const selectedModelLabel = computed(() => {
  const id = selectedModelId.value;
  for (const provider of providers.value) {
    for (const model of provider.models) {
      if (model.id === id) {
        return `${provider.name} / ${model.name}`;
      }
    }
  }
  // 如果列表未加载，显示原始值
  const { provider, name } = conversationStore.currentModel;
  return `${provider} / ${name}`;
});

// 加载模型列表
const loadModels = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await getModels();
    providers.value = response.providers;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "加载模型列表失败";
    console.error("Failed to load models:", e);
  } finally {
    loading.value = false;
  }
};

// 组件挂载时加载模型列表
onMounted(() => {
  loadModels();
});

// 暴露刷新方法
defineExpose({
  refresh: loadModels,
});
</script>

<template>
  <div class="inline-flex">
    <!-- 加载中状态 -->
    <div v-if="loading" class="flex items-center gap-2">
      <Skeleton class="h-8 w-40" />
    </div>

    <!-- 错误状态 -->
    <div
      v-else-if="error"
      class="text-destructive text-sm"
      :title="error"
    >
      加载失败
    </div>

    <!-- 正常状态 -->
    <Select v-else v-model="selectedModelId">
      <SelectTrigger class="w-auto min-w-40" data-testid="model-selector">
        <SelectValue>
          {{ selectedModelLabel }}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectGroup
          v-for="provider in providers"
          :key="provider.id"
        >
          <SelectLabel>{{ provider.name }}</SelectLabel>
          <SelectItem
            v-for="model in provider.models"
            :key="model.id"
            :value="model.id"
          >
            {{ model.name }}
          </SelectItem>
        </SelectGroup>

        <!-- 空状态 -->
        <div
          v-if="providers.length === 0"
          class="text-muted-foreground px-2 py-4 text-center text-sm"
        >
          暂无可用模型
        </div>
      </SelectContent>
    </Select>
  </div>
</template>
