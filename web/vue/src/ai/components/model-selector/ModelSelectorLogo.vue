<script setup lang="ts">
import type { HTMLAttributes } from "vue";

import { cn } from "@/lib/utils";

interface Props {
  class?: HTMLAttributes["class"];
  provider: string;
  src?: string; // 新增：可选的图标 URL
}

const props = defineProps<Props>();

// 处理图标加载错误
const handleLogoError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = "none";
};
</script>

<template>
  <img
    v-if="props.src"
    v-bind="$attrs"
    :alt="`${props.provider} logo`"
    :class="cn('size-3 dark:invert', props.class)"
    height="12"
    :src="props.src"
    width="12"
    @error="handleLogoError"
  />
</template>
