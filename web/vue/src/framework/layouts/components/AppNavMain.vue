<script setup lang="ts">
/**
 * AppNavMain 分组菜单组件
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

interface AppNavItem {
  icon?: FunctionalComponent;
  title: string;
  url: string;
}

interface AppNavSubItem {
  title: string;
  url: string;
}

interface AppNavSub {
  icon?: FunctionalComponent;
  title: string;
  items: AppNavSubItem[];
}

interface AppNavGroup {
  title?: string;
  items: Array<AppNavItem | AppNavSub>;
}

const props = withDefaults(
  defineProps<{
    items?: AppNavGroup[];
  }>(),
  {
    items: () => [],
  }
);

const route = useRoute();
const router = useRouter();

const defaultItems: AppNavGroup[] = [
  {
    items: [
      { icon: Home, title: "首页", url: "/" },
      { icon: Activity, title: "健康检查", url: "/health" },
      { icon: Database, title: "知识库", url: "/datasets" },
    ],
  },
  {
    title: "系统管理",
    items: [
      {
        icon: Settings,
        title: "IAM",
        items: [
          { title: "用户管理", url: "/iam/users" },
          { title: "角色管理", url: "/iam/roles" },
          { title: "部门管理", url: "/iam/departments" },
          { title: "租户管理", url: "/iam/tenants" },
          { title: "权限管理", url: "/iam/permissions" },
        ],
      },
    ],
  },
];

const menuItems = computed(() =>
  props.items.length > 0 ? props.items : defaultItems
);

const expandedMenus = ref<string[]>([]);

const isItemActive = (url: string) => route.path === url;

const isSubActive = (sub: AppNavSub) =>
  sub.items.some((item) => route.path.startsWith(item.url));

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
          <SidebarMenuItem v-if="'url' in item">
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
          <SidebarMenuItem v-else>
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
                      @click="handleNavigate(subItem.url)"
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
