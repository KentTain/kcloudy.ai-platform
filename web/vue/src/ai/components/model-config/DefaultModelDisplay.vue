<script setup lang="ts">
/**
 * 模型配置 - 默认模型只读展示
 */
import { Badge } from "@/components";
import { Card } from "@/components/ui/card";
import type { DefaultModelItem, ModelTypeKey } from "@/ai/types/modelConfig";
import { MODEL_TYPE_LABELS } from "@/ai/types/modelConfig";

defineProps<{
  defaultModels: DefaultModelItem[];
}>();

const displayTypes: ModelTypeKey[] = ["llm", "text-embedding", "rerank"];

function getDefaultModel(models: DefaultModelItem[], type: ModelTypeKey): DefaultModelItem | undefined {
  return models.find((m) => m.model_type === type && m.is_valid);
}
</script>

<template>
  <Card class="p-4">
    <div class="mb-2 text-sm font-medium text-muted-foreground">默认模型配置</div>
    <div class="flex flex-wrap gap-4">
      <div
        v-for="type in displayTypes"
        :key="type"
        class="flex items-center gap-2"
      >
        <Badge variant="outline">{{ MODEL_TYPE_LABELS[type] }}</Badge>
        <template v-if="getDefaultModel(defaultModels, type)">
          <span class="text-sm font-medium">
            {{ getDefaultModel(defaultModels, type)?.model_name || "未命名" }}
          </span>
        </template>
        <span v-else class="text-sm text-muted-foreground">未配置</span>
      </div>
    </div>
  </Card>
</template>
