<script setup lang="ts">
/**
 * AppSidebar 侧边栏组件
 */
import { computed, ref } from "vue";
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
  {
    name: "系统管理",
    path: "/iam",
    icon: "settings",
    children: [
      { name: "用户管理", path: "/iam/users", icon: "user" },
      { name: "角色管理", path: "/iam/roles", icon: "role" },
      { name: "部门管理", path: "/iam/departments", icon: "department" },
      { name: "租户管理", path: "/iam/tenants", icon: "tenant" },
      { name: "权限管理", path: "/iam/permissions", icon: "permission" },
    ],
  },
];

const menus = computed(() => props.menus || defaultMenus);

const isActive = (path: string) => route.path === path;
const isParentActive = (item: MenuItem) => {
  if (item.children) {
    return item.children.some((child) => route.path.startsWith(child.path));
  }
  return route.path.startsWith(item.path);
};

const expandedMenus = ref<string[]>([]);

const toggleExpand = (path: string) => {
  const index = expandedMenus.value.indexOf(path);
  if (index > -1) {
    expandedMenus.value.splice(index, 1);
  } else {
    expandedMenus.value.push(path);
  }
};

const handleClick = (item: MenuItem) => {
  if (item.children) {
    toggleExpand(item.path);
  } else if (item.path) {
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
        :class="[
          'app-sidebar__menu-item',
          {
            'app-sidebar__menu-item--active': isParentActive(item),
            'app-sidebar__menu-item--expanded': expandedMenus.includes(item.path),
          },
        ]"
      >
        <div class="app-sidebar__menu-item-content" @click="handleClick(item)">
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
            <svg v-else-if="item.icon === 'settings'" viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          </span>
          <span v-if="!appStore.sidebarCollapsed" class="app-sidebar__menu-text">{{ item.name }}</span>
          <svg
            v-if="item.children && !appStore.sidebarCollapsed"
            class="app-sidebar__menu-arrow"
            :class="{ 'app-sidebar__menu-arrow--expanded': expandedMenus.includes(item.path) }"
            viewBox="0 0 24 24"
            width="16"
            height="16"
          >
            <path fill="currentColor" d="M7 10l5 5 5-5z" />
          </svg>
        </div>

        <!-- 子菜单 -->
        <div
          v-if="item.children && !appStore.sidebarCollapsed && expandedMenus.includes(item.path)"
          class="app-sidebar__submenu"
        >
          <div
            v-for="child in item.children"
            :key="child.path"
            :class="['app-sidebar__submenu-item', { 'app-sidebar__submenu-item--active': isActive(child.path) }]"
            @click="router.push(child.path)"
          >
            <span class="app-sidebar__submenu-dot"></span>
            <span>{{ child.name }}</span>
          </div>
        </div>
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

.app-sidebar__menu-item-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.app-sidebar__menu-arrow {
  margin-left: auto;
  transition: transform var(--transition-fast);
}

.app-sidebar__menu-arrow--expanded {
  transform: rotate(180deg);
}

.app-sidebar__submenu {
  margin-top: 0.25rem;
  padding-left: 2rem;
}

.app-sidebar__submenu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  margin: 0.125rem 0.5rem;
  border-radius: var(--radius-ui);
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  transition: all var(--transition-fast);
}

.app-sidebar__submenu-item:hover {
  color: var(--color-primary);
  background-color: var(--color-surface);
}

.app-sidebar__submenu-item--active {
  color: var(--color-primary);
}

.app-sidebar__submenu-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
  opacity: 0.5;
}

.app-sidebar__submenu-item--active .app-sidebar__submenu-dot {
  opacity: 1;
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
