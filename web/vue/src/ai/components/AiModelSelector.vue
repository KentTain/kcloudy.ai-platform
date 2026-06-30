<script setup lang="ts">
/**
 * AI 模型选择器组件
 *
 * 提供完整的模型选择功能，包括：
 * - 按提供商分组的模型列表
 * - 提供商 Logo 显示
 * - 搜索过滤
 * - 默认模型管理
 */
import { ref, computed, onMounted } from "vue";
import { CheckIcon } from "lucide-vue-next";
import {
  ModelSelector,
  ModelSelectorContent,
  ModelSelectorEmpty,
  ModelSelectorGroup,
  ModelSelectorInput,
  ModelSelectorItem,
  ModelSelectorList,
  ModelSelectorName,
  ModelSelectorTrigger,
} from "@/ai/components/model-selector";
import { Button } from "@/components";
import { useConversationStore } from "@/ai/stores";
import type { ModelItem, ProviderItem } from "@/ai/api/model";
import type { ModelConfig } from "@/ai/types";

const conversationStore = useConversationStore();
const modelSelectorOpen = ref(false);

// 当前选中的模型
const selectedModel = computed(() => {
  const { provider, name } = conversationStore.currentModel;
  for (const p of conversationStore.providers) {
    for (const m of p.models) {
      if (m.id === `${provider}/${name}`) {
        return m;
      }
    }
  }
  return null;
});

// 当前选中的提供商
const selectedProvider = computed(() => {
  if (!selectedModel.value) return null;
  return conversationStore.providers.find(
    (p) => p.id === conversationStore.currentModel.provider
  );
});

// 判断模型是否选中
const isSelected = (model: ModelItem) => {
  return (
    model.id ===
    `${conversationStore.currentModel.provider}/${conversationStore.currentModel.name}`
  );
};

// 选择模型
const onModelSelect = (model: ModelItem, provider: ProviderItem) => {
  conversationStore.setModel({
    provider: provider.id,
    name: model.name,
  } as ModelConfig);
  modelSelectorOpen.value = false;
};

// 组件挂载时加载模型列表和默认模型
onMounted(async () => {
  await conversationStore.fetchModels();
  await conversationStore.fetchDefaultModel("llm");
});
</script>

<template>
  <ModelSelector v-model:open="modelSelectorOpen">
    <ModelSelectorTrigger as-child>
      <Button variant="ghost" size="sm" class="gap-2">
        <template v-if="selectedModel">
          <img
            v-if="selectedProvider?.icon_small"
            class="size-3 dark:invert"
            :src="selectedProvider.icon_small"
            alt="provider logo"
          />
          <ModelSelectorName v-if="selectedModel.label">
            {{ selectedModel.label }}
          </ModelSelectorName>
          <ModelSelectorName v-else>
            {{ selectedModel.name }}
          </ModelSelectorName>
        </template>
        <template v-else>
          请选择模型
        </template>
      </Button>
    </ModelSelectorTrigger>

    <ModelSelectorContent>
      <ModelSelectorInput placeholder="搜索模型..." />
      <ModelSelectorList>
        <ModelSelectorEmpty>无任何模型.</ModelSelectorEmpty>

        <ModelSelectorGroup
          v-for="provider in conversationStore.providers"
          :key="provider.id"
          :heading="provider.name"
        >
          <ModelSelectorItem
            v-for="model in provider.models"
            :key="model.id"
            :value="model.id"
            @select="() => onModelSelect(model, provider)"
          >
            <img
              v-if="provider?.icon_small"
              class="size-3 dark:invert"
              :src="provider.icon_small"
              alt="provider logo"
            />
            <ModelSelectorName>{{ model.label || model.name }}</ModelSelectorName>

            <CheckIcon v-if="isSelected(model)" class="ml-auto size-4" />
            <div v-else class="ml-auto size-4" />
          </ModelSelectorItem>
        </ModelSelectorGroup>
      </ModelSelectorList>
    </ModelSelectorContent>
  </ModelSelector>
</template>
