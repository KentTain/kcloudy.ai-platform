<script setup lang="ts">
/**
 * AppNavMain 分组菜单组件
 * 支持权限过滤
 */
import type { FunctionalComponent } from "vue";
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ChevronRight,
  Home,
  Activity,
  Database,
  Settings,
} from "@lucide/vue";
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

interface MenuItem {
  icon?: FunctionalComponent;
  title: string;
  url?: string;
  permissionKey?: string;
  items?: MenuItem[];
}

interface MenuGroup {
  title?: string;
  items: MenuItem[];
}

const props = withDefaults(
  defineProps<{
    items?: MenuGroup[];
  }>(),
  {
    items: () => [],
  }
);

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const defaultItems: MenuGroup[] = [
  {
    items: [
      { icon: Home, title: "首页", url: "/", permissionKey: "home" },
      { icon: Activity, title: "健康检查", url: "/health", permissionKey: "health" },
      { icon: Database, title: "知识库", url: "/datasets", permissionKey: "datasets" },
    ],
  },
  {
    title: "系统管理",
    items: [
      {
        icon: Settings,
        title: "IAM",
        permissionKey: "iam",
        items: [
          { title: "用户管理", url: "/iam/users", permissionKey: "iam.users" },
          { title: "角色管理", url: "/iam/roles", permissionKey: "iam.roles" },
          { title: "部门管理", url: "/iam/departments", permissionKey: "iam.departments" },
          { title: "租户管理", url: "/iam/tenants", permissionKey: "iam.tenants" },
          { title: "权限管理", url: "/iam/permissions", permissionKey: "iam.permissions" },
        ],
      },
    ],
  },
];

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

const rawMenuItems = computed(() =>
  props.items.length > 0 ? props.items : defaultItems
);

const menuItems = computed(() => filterMenuGroups(rawMenuItems.value));

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
</script>

<template>
  <SidebarGroup v-for="(group, groupIndex) in menuItems" :key="groupIndex">
    <SidebarGroupLabel v-if="group.title">{{ group.title }}</SidebarGroupLabel>
    <SidebarGroupContent>
      <SidebarMenu>
        <template v-for="(item, itemIndex) in group.items" :key="itemIndex">
          <!-- 无子菜单的菜单项 -->
          <SidebarMenuItem v-if="item.url">
            <SidebarMenuButton
              :tooltip="item.title"
              :is-active="isItemActive(item.url)"
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
                <SidebarMenuButton :tooltip="item.title">
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
