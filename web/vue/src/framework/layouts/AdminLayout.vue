<script setup lang="ts">
/**
 * AdminLayout 后台管理布局组件
 */
import { computed, onMounted, onUnmounted } from "vue";
import { useAppStore } from "@/framework/stores";
import AppSidebar from "./components/AppSidebar.vue";
import AppNavbar from "./components/AppNavbar.vue";
import AppTagsView from "./components/AppTagsView.vue";
import AppMain from "./components/AppMain.vue";

const appStore = useAppStore();

const sidebarWidth = computed(() => (appStore.sidebarCollapsed ? "64px" : "240px"));

const MOBILE_BREAKPOINT = 768;

const syncDeviceFromViewport = () => {
  appStore.setDevice(window.innerWidth < MOBILE_BREAKPOINT ? "mobile" : "desktop");
};

onMounted(() => {
  syncDeviceFromViewport();
  window.addEventListener("resize", syncDeviceFromViewport);
});

onUnmounted(() => {
  window.removeEventListener("resize", syncDeviceFromViewport);
});
</script>

<template>
  <div class="admin-layout">
    <AppSidebar class="admin-layout__sidebar" :style="{ width: sidebarWidth }" />
    <div class="admin-layout__main" :style="{ marginLeft: sidebarWidth }">
      <AppNavbar class="admin-layout__navbar" />
      <AppTagsView class="admin-layout__tagsview" />
      <AppMain class="admin-layout__content" />
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--color-surface);
}

.admin-layout__sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  transition: width var(--transition-normal);
  z-index: 100;
}

.admin-layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left var(--transition-normal);
}

.admin-layout__navbar {
  height: 60px;
  flex-shrink: 0;
}

.admin-layout__tagsview {
  height: 32px;
  flex-shrink: 0;
}

.admin-layout__content {
  flex: 1;
  overflow: auto;
}

@media (max-width: 768px) {
  .admin-layout__sidebar {
    transform: translateX(-100%);
  }

  .admin-layout__main {
    margin-left: 0 !important;
  }
}
</style>
