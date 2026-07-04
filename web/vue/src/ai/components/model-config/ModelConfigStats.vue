<script setup lang="ts">
/**
 * 模型配置 - 统计卡片
 */
import { Card } from "@/components/ui/card";
import { Package, Check, Cpu } from "lucide-vue-next";

defineProps<{
  totalPlugins: number;
  configuredPlugins: number;
  totalModels: number;
}>();
</script>

<template>
  <div class="grid grid-cols-3 gap-4">
    <Card class="p-4">
      <div class="flex items-center gap-4">
        <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
          <Package class="h-6 w-6 text-primary" />
        </div>
        <div>
          <div class="text-2xl font-bold">{{ totalPlugins }}</div>
          <div class="text-sm text-muted-foreground">插件总数</div>
        </div>
      </div>
    </Card>
    <Card class="p-4">
      <div class="flex items-center gap-4">
        <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/10">
          <Check class="h-6 w-6 text-green-500" />
        </div>
        <div>
          <div class="text-2xl font-bold">{{ configuredPlugins }}</div>
          <div class="text-sm text-muted-foreground">已配置模型</div>
        </div>
      </div>
    </Card>
    <Card class="p-4">
      <div class="flex items-center gap-4">
        <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-500/10">
          <Cpu class="h-6 w-6 text-amber-500" />
        </div>
        <div>
          <div class="text-2xl font-bold">{{ totalModels }}</div>
          <div class="text-sm text-muted-foreground">模型总数</div>
        </div>
      </div>
    </Card>
  </div>
</template>
