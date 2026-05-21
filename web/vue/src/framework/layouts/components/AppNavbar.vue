<script setup lang="ts">
/**
 * AppNavbar 顶部导航组件
 */
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAppStore, useUserStore } from "@/framework/stores";

const route = useRoute();
const appStore = useAppStore();
const userStore = useUserStore();

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title);
  return matched.map((item) => ({
    title: item.meta?.title as string,
    path: item.path,
  }));
});

const toggleSidebar = () => {
  appStore.toggleSidebar();
};
</script>

<template>
  <header class="app-navbar">
    <div class="app-navbar__left">
      <button class="app-navbar__toggle" @click="toggleSidebar">
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
        </svg>
      </button>

      <nav v-if="breadcrumbs.length > 0" class="app-navbar__breadcrumb">
        <template v-for="(item, index) in breadcrumbs" :key="item.path">
          <span v-if="index > 0" class="app-navbar__breadcrumb-separator">/</span>
          <span
            :class="[
              'app-navbar__breadcrumb-item',
              { 'app-navbar__breadcrumb-item--last': index === breadcrumbs.length - 1 },
            ]"
          >
            {{ item.title }}
          </span>
        </template>
      </nav>
    </div>

    <div class="app-navbar__right">
      <button class="app-navbar__action" title="全屏">
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
        </svg>
      </button>

      <button class="app-navbar__action" title="消息">
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path fill="currentColor" d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
        </svg>
      </button>

      <div class="app-navbar__user">
        <div class="app-navbar__avatar">
          {{ userStore.userInfo?.nickname?.charAt(0) || "U" }}
        </div>
        <span class="app-navbar__username">{{ userStore.userInfo?.nickname || "用户" }}</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  background-color: var(--color-surface-raised);
  border-bottom: 1px solid var(--color-border);
}

.app-navbar__left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-navbar__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-ui);
  transition: all var(--transition-fast);
}

.app-navbar__toggle:hover {
  color: var(--color-primary);
  background-color: var(--color-surface);
}

.app-navbar__breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.app-navbar__breadcrumb-separator {
  color: var(--color-text-disabled);
}

.app-navbar__breadcrumb-item {
  color: var(--color-text-muted);
}

.app-navbar__breadcrumb-item--last {
  color: var(--color-text);
}

.app-navbar__right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.app-navbar__action {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-ui);
  transition: all var(--transition-fast);
}

.app-navbar__action:hover {
  color: var(--color-primary);
  background-color: var(--color-surface);
}

.app-navbar__user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  border-radius: var(--radius-ui);
  transition: background-color var(--transition-fast);
}

.app-navbar__user:hover {
  background-color: var(--color-surface);
}

.app-navbar__avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-primary);
  color: white;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 500;
}

.app-navbar__username {
  font-size: 0.875rem;
  color: var(--color-text);
}
</style>
