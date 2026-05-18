<script setup lang="ts">
interface Props {
  size?: "sm" | "md" | "lg";
}

withDefaults(defineProps<Props>(), {
  size: "md",
});

// biome-ignore lint/correctness/noUnusedVariables: used in template
const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-8 w-8",
  lg: "h-12 w-12",
};
</script>

<template>
  <div class="flex items-center justify-center">
    <div
      :class="[
        'animate-spin rounded-full border-4 border-gray-200 border-t-blue-600',
        sizeClasses[size],
      ]"
    />
  </div>
</template>