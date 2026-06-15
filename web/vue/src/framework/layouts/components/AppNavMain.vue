<script setup lang="ts">
/**
 * AppNavMain 分组菜单组件
 * 从后端获取用户菜单，支持权限过滤
 */
import type { FunctionalComponent } from "vue";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import * as LucideIcons from "@lucide/vue";
import { ChevronRight } from "@lucide/vue";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { useUserStore } from "@/framework/stores/user";
import { useMenuStore, type UserMenuItem } from "@/framework/stores/menu";

/**
 * 默认图标（当指定图标不存在时使用）
 */
const DEFAULT_ICON = LucideIcons.Folder;

/**
 * 获取图标组件
 * @param iconName 图标名称
 * @returns 图标组件或默认图标
 */
function getIconComponent(iconName: string | null | undefined): FunctionalComponent | undefined {
  if (!iconName) return undefined;

  // 尝试从 Lucide 图标库获取
  const icon = (LucideIcons as Record<string, FunctionalComponent>)[iconName];
  return icon || DEFAULT_ICON;
}

/**
 * 内部菜单项接口
 */
interface MenuItem {
  icon?: FunctionalComponent;
  title: string;
  url?: string;
  permissionKey?: string;
  items?: MenuItem[];
}

/**
 * 内部菜单分组接口
 */
interface MenuGroup {
  title?: string;
  items: MenuItem[];
}

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const menuStore = useMenuStore();

/**
 * 将 UserMenuItem 转换为内部 MenuItem
 */
function convertToMenuItem(item: UserMenuItem): MenuItem {
  const icon = getIconComponent(item.icon);
  const children = item.children?.map(convertToMenuItem) || [];

  return {
    icon,
    title: item.name,
    url: item.path || undefined,
    permissionKey: item.code,
    items: children.length > 0 ? children : undefined,
  };
}

/**
 * 将用户菜单转换为分组结构
 * 第一级菜单作为分组，第二级作为菜单项
 */
function convertToMenuGroups(items: UserMenuItem[]): MenuGroup[] {
  return items.map((item) => {
    const children = item.children?.map(convertToMenuItem) || [];

    // 如果有子菜单，第一级作为分组
    if (children.length > 0) {
      return {
        title: item.name,
        items: children,
      };
    }

    // 如果没有子菜单，作为顶级菜单项
    const icon = getIconComponent(item.icon);
    return {
      items: [{
        icon,
        title: item.name,
        url: item.path || undefined,
        permissionKey: item.code,
      }],
    };
  });
}

// 权限检查函数
function hasPermissionKey(permissionKey: string | undefined): boolean {
  if (!permissionKey) return true;
  const userPermissions = userStore.userInfo?.permissions || [];
  if (userPermissions.length === 0) return true;

  if (userPermissions.includes(permissionKey)) return true;

  // 层级匹配
  const parts = permissionKey.split(".");
  for (let i = parts.length - 1; i > 0; i--) {
    const parentKey = parts.slice(0, i).join(".");
    if (userPermissions.includes(parentKey)) return true;
  }

  return false;
}

// 过滤菜单项
function filterMenuItem(item: MenuItem): MenuItem | null {
  if (!hasPermissionKey(item.permissionKey)) return null;

  if (item.items) {
    const filteredItems = item.items
      .map(filterMenuItem)
      .filter((i): i is MenuItem => i !== null);
    if (filteredItems.length === 0) return null;
    return { ...item, items: filteredItems };
  }

  return item;
}

// 过滤菜单分组
function filterMenuGroups(groups: MenuGroup[]): MenuGroup[] {
  return groups
    .map((group) => {
      const filteredItems = group.items
        .map(filterMenuItem)
        .filter((i): i is MenuItem => i !== null);
      if (filteredItems.length === 0) return null;
      return { ...group, items: filteredItems };
    })
    .filter((g): g is MenuGroup => g !== null);
}

// 计算菜单项
const menuItems = computed(() => {
  const userMenus = menuStore.userMenus;

  if (userMenus.length === 0) {
    return [];
  }

  const groups = convertToMenuGroups(userMenus);
  return filterMenuGroups(groups);
});

// 加载状态
const loading = computed(() => menuStore.loading);

// 是否有菜单
const hasMenus = computed(() => menuItems.value.length > 0);

const expandedMenus = ref<string[]>([]);

const isItemActive = (url: string | undefined): boolean | undefined => {
  if (!url) return undefined;
  return route.path === url;
};

const isSubActive = (item: MenuItem): boolean =>
  item.items?.some((sub) => sub.url && route.path.startsWith(sub.url)) ?? false;

const toggleExpand = (title: string) => {
  const index = expandedMenus.value.indexOf(title);
  if (index > -1) {
    expandedMenus.value.splice(index, 1);
  } else {
    expandedMenus.value.push(title);
  }
};

const handleNavigate = (url: string) => {
  router.push(url);
};

// 组件挂载时获取菜单
onMounted(() => {
  if (menuStore.userMenus.length === 0) {
    menuStore.fetchUserMenus();
  }
});
</script>

<template>
  <!-- 加载状态 -->
  <div v-if="loading" class="p-4 text-center text-muted-foreground">
    加载菜单中...
  </div>

  <!-- 无菜单提示 -->
  <div v-else-if="!hasMenus" class="p-4 text-center text-muted-foreground">
    暂无可用菜单
  </div>

  <!-- 菜单列表 -->
  <SidebarGroup v-for="(group, groupIndex) in menuItems" :key="groupIndex">
    <SidebarGroupLabel v-if="group.title" class="mb-3 h-5 text-gray-500">{{ group.title }}</SidebarGroupLabel>
    <SidebarGroupContent>
      <SidebarMenu>
        <template v-for="(item, itemIndex) in group.items" :key="itemIndex">
          <!-- 无子菜单的菜单项 -->
          <SidebarMenuItem v-if="item.url">
            <SidebarMenuButton
              :tooltip="item.title"
              :is-active="isItemActive(item.url)"
              class="h-10 hover:bg-accent-foreground/5"
              :class="isItemActive(item.url) ? 'bg-white! text-primary!' : ''"
              @click="handleNavigate(item.url)"
            >
              <component :is="item.icon" v-if="item.icon" />
              <span>{{ item.title }}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>

          <!-- 有子菜单的菜单项 -->
          <SidebarMenuItem v-else-if="item.items">
            <Collapsible
              :open="expandedMenus.includes(item.title) || isSubActive(item)"
              @update:open="toggleExpand(item.title)"
            >
              <CollapsibleTrigger as-child>
                <SidebarMenuButton :tooltip="item.title" class="h-10 hover:bg-accent-foreground/5">
                  <component :is="item.icon" v-if="item.icon" />
                  <span>{{ item.title }}</span>
                  <ChevronRight
                    class="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90"
                  />
                </SidebarMenuButton>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarMenuSub>
                  <SidebarMenuSubItem
                    v-for="(subItem, subIndex) in item.items"
                    :key="subIndex"
                  >
                    <SidebarMenuSubButton
                      :is-active="isItemActive(subItem.url)"
                      @click="subItem.url && handleNavigate(subItem.url)"
                    >
                      <span>{{ subItem.title }}</span>
                    </SidebarMenuSubButton>
                  </SidebarMenuSubItem>
                </SidebarMenuSub>
              </CollapsibleContent>
            </Collapsible>
          </SidebarMenuItem>
        </template>
      </SidebarMenu>
    </SidebarGroupContent>
  </SidebarGroup>
</template>
