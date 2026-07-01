<script setup lang="ts">
/**
 * App 根组件
 */
import { Toaster } from "@/components/ui/sonner"
</script>

<template>
  <router-view />
  <Toaster position="top-center" rich-colors :visibleToasts="3" />
</template>

<style>
/* Tailwind v4 已在 @layer base 中提供重置样式，此处无需重复定义 */

html,
body,
#app {
  height: 100%;
}
</style>
