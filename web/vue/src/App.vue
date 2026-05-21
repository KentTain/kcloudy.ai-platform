<script setup lang="ts">
/**
 * App 根组件
 */
import AdminLayout from "@/framework/layouts/AdminLayout.vue";
</script>

<template>
  <AdminLayout />
</template>

<style>
/* 全局样式重置 */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body {
  height: 100%;
}

#app {
  height: 100%;
}
</style>
