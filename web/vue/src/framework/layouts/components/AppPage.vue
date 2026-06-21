<script setup lang="ts">
/**
 * AppPage 页面骨架组件
 * 统一所有业务页面的 title/eyebrow/description/actions 区域
 */
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    eyebrow?: string;
    description?: string;
    variant?: "list" | "workbench" | "detail" | "governance";
  }>(),
  {
    variant: "list",
  },
);

const containerClass = computed(() => {
  const base = "h-full min-h-0 flex flex-col";
  if (props.variant === "workbench") return `${base} bg-muted/20`;
  return `${base} bg-background`;
});
</script>

<template>
  <main :class="containerClass">
    <div class="flex h-full min-h-0 flex-col gap-3 p-4 md:p-6">
      <!-- 标题区域 -->
      <div class="shrink-0 flex flex-wrap items-center justify-between gap-2">
        <div class="min-w-0 space-y-0.5">
          <p v-if="eyebrow" class="text-muted-foreground text-xs font-medium">{{ eyebrow }}</p>
          <h1 class="truncate text-xl font-semibold tracking-normal">{{ title }}</h1>
          <p v-if="description" class="text-muted-foreground max-w-3xl text-sm">{{ description }}</p>
        </div>
        <div v-if="$slots.actions" class="flex shrink-0 flex-wrap items-center gap-2">
          <slot name="actions" />
        </div>
      </div>
      <!-- 内容区域 -->
      <slot />
    </div>
  </main>
</template>
