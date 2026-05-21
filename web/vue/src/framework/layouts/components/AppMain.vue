<script setup lang="ts">
/**
 * AppMain 内容区组件
 */
</script>

<template>
  <main class="app-main">
    <router-view v-slot="{ Component, route }">
      <transition name="app-main-fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </main>
</template>

<style scoped>
.app-main {
  padding: 1rem;
  background-color: var(--color-surface);
  min-height: 0;
}

.app-main-fade-enter-active,
.app-main-fade-leave-active {
  transition: opacity 0.3s ease;
}

.app-main-fade-enter-from,
.app-main-fade-leave-to {
  opacity: 0;
}
</style>
