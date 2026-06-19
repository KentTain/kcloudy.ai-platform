<script setup lang="ts">
/**
 * Loading 加载组件
 * 保留手写实现，调整为使用 CSS 变量令牌
 */
import { LoaderIcon } from "@lucide/vue";
import { cn } from "@/lib/utils";

interface Props {
  size?: "sm" | "md" | "lg";
  text?: string;
  fullscreen?: boolean;
}

withDefaults(defineProps<Props>(), {
  size: "md",
  fullscreen: false,
});

const sizeClasses: Record<string, string> = {
  sm: "size-4",
  md: "size-8",
  lg: "size-12",
};
</script>

<template>
  <div
    :class="cn(
      'flex flex-col items-center justify-center gap-2',
      fullscreen && 'fixed inset-0 bg-background/90 z-[9999]'
    )"
  >
    <LoaderIcon :class="cn('animate-spin text-primary', sizeClasses[size])" />
    <span v-if="text" class="text-sm text-muted-foreground">{{ text }}</span>
  </div>
</template>
