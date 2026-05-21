<script setup lang="ts">
/**
 * AppSidebar 侧边栏组件
 */
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAppStore } from "@/framework/stores";

interface MenuItem {
  name: string;
  path: string;
  icon?: string;
  children?: MenuItem[];
}

const props = defineProps<{
  menus?: MenuItem[];
}>();

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();

const defaultMenus: MenuItem[] = [
  { name: "首页", path: "/", icon: "home" },
  { name: "健康检查", path: "/health", icon: "health" },
  { name: "知识库", path: "/datasets", icon: "database" },
];

const menus = computed(() => props.menus || defaultMenus);

const isActive = (path: string) => route.path === path;

const handleClick = (item: MenuItem) => {
  if (item.path) {
    router.push(item.path);
  }
};

const toggleCollapse = () => {
  appStore.toggleSidebar();
};
</script>

<template>
  <aside class="app-sidebar">
    <div class="app-sidebar__logo">
      <span v-if="!appStore.sidebarCollapsed" class="app-sidebar__logo-text">AI 助手平台</span>
      <span v-else class="app-sidebar__logo-icon">AI</span>
    </div>

    <nav class="app-sidebar__menu">
      <div
        v-for="item in menus"
        :key="item.path"
        :class="['app-sidebar__menu-item', { 'app-sidebar__menu-item--active': isActive(item.path) }]"
        @click="handleClick(item)"
      >
        <span class="app-sidebar__menu-icon">
          <svg v-if="item.icon === 'home'" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
          </svg>
          <svg v-else-if="item.icon === 'health'" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
          <svg v-else-if="item.icon === 'database'" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 3C7.58 3 4 4.79 4 7v10c0 2.21 3.58 4 8 4s8-1.79 8-4V7c0-2.21-3.58-4-8-4zm0 2c3.87 0 6 1.5 6 2s-2.13 2-6 2-6-1.5-6-2 2.13-2 6-2zm6 12c0 .5-2.13 2-6 2s-6-1.5-6-2v-2.23c1.61.78 3.72 1.23 6 1.23s4.39-.45 6-1.23V17zm0-5c0 .5-2.13 2-6 2s-6-1.5-6-2V9.77c1.61.78 3.72 1.23 6 1.23s4.39-.45 6-1.23V12z" />
          </svg>
        </span>
        <span v-if="!appStore.sidebarCollapsed" class="app-sidebar__menu-text">{{ item.name }}</span>
      </div>
    </nav>

    <div class="app-sidebar__footer">
      <button class="app-sidebar__toggle" @click="toggleCollapse">
        <svg
          viewBox="0 0 24 24"
          width="20"
          height="20"
          :style="{ transform: appStore.sidebarCollapsed ? 'rotate(180deg)' : '' }"
        >
          <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--color-surface-raised);
  border-right: 1px solid var(--color-border);
}

.app-sidebar__logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
  font-size: 1.125rem;
  color: var(--color-primary);
}

.app-sidebar__logo-text {
  white-space: nowrap;
  overflow: hidden;
}

.app-sidebar__logo-icon {
  font-weight: 700;
}

.app-sidebar__menu {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
}

.app-sidebar__menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  margin: 0.25rem 0.5rem;
  border-radius: var(--radius-ui);
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
  position: relative;
}

.app-sidebar__menu-item:hover {
  color: var(--color-primary);
  background-color: var(--color-surface);
}

.app-sidebar__menu-item--active {
  color: var(--color-primary);
  background-color: var(--color-primary-subtle);
}

.app-sidebar__menu-item--active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background-color: var(--color-primary);
  border-radius: 0 2px 2px 0;
}

.app-sidebar__menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.app-sidebar__menu-text {
  white-space: nowrap;
  overflow: hidden;
}

.app-sidebar__footer {
  padding: 0.5rem;
  border-top: 1px solid var(--color-border);
}

.app-sidebar__toggle {
  width: 100%;
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

.app-sidebar__toggle:hover {
  color: var(--color-primary);
  background-color: var(--color-surface);
}

.app-sidebar__toggle svg {
  transition: transform var(--transition-fast);
}
</style>
