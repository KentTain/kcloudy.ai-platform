<script setup lang="ts">
/**
 * AppNavbar 顶部导航组件
 * 包含 SidebarTrigger、面包屑、水平导航、搜索触发和快捷按钮
 */
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { SearchIcon, ClipboardCheckIcon, BellIcon } from "@lucide/vue";
import { Button } from "@/components";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { useCommandPalette } from "@/framework/composables/useCommandPalette";

const route = useRoute();
const router = useRouter();
const { openCommandPalette } = useCommandPalette();

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title);
  return matched.map((item) => ({
    title: item.meta?.title as string,
    path: item.path,
  }));
});

// 水平导航菜单项
const navItems = [
  { title: "首页", url: "/" },
  { title: "知识库", url: "/datasets" },
];

// 当前激活的导航项
const isActiveNav = (url: string) => {
  if (url === "/") return route.path === "/";
  return route.path.startsWith(url);
};

function navigateTo(url: string) {
  router.push(url);
}
</script>

<template>
  <header class="flex h-14 items-center gap-2 border-b bg-background px-4">
    <SidebarTrigger />
    <Separator orientation="vertical" class="h-6 mr-2" />

    <!-- 面包屑 -->
    <Breadcrumb v-if="breadcrumbs.length > 0" class="hidden md:block">
      <BreadcrumbList>
        <template v-for="(item, index) in breadcrumbs" :key="item.path">
          <BreadcrumbItem v-if="index < breadcrumbs.length - 1">
            <BreadcrumbLink as-child>
              <RouterLink :to="item.path">{{ item.title }}</RouterLink>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator v-if="index < breadcrumbs.length - 1" />
          <BreadcrumbItem v-if="index === breadcrumbs.length - 1">
            <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
          </BreadcrumbItem>
        </template>
      </BreadcrumbList>
    </Breadcrumb>

    <!-- 水平导航 -->
    <NavigationMenu class="hidden lg:flex ml-4">
      <NavigationMenuList>
        <NavigationMenuItem v-for="item in navItems" :key="item.url">
          <NavigationMenuLink
            as-child
            :class="[navigationMenuTriggerStyle(), isActiveNav(item.url) ? 'bg-accent' : '']"
          >
            <RouterLink :to="item.url">{{ item.title }}</RouterLink>
          </NavigationMenuLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>

    <!-- 右侧区域：搜索 + 快捷按钮 -->
    <div class="ml-auto flex items-center gap-2">
      <!-- 搜索触发区域 -->
      <button
        type="button"
        class="inline-flex items-center gap-2 whitespace-nowrap rounded-md border border-input bg-background px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        @click="openCommandPalette"
      >
        <SearchIcon class="size-4" />
        <span class="hidden sm:inline">搜索...</span>
        <kbd class="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-xs font-medium sm:flex">
          <span class="text-xs">⌘</span>K
        </kbd>
      </button>

      <!-- 快捷按钮 -->
      <Button variant="ghost" size="icon" @click="navigateTo('/admin/todos')">
        <ClipboardCheckIcon class="size-4" />
      </Button>
      <Button variant="ghost" size="icon" @click="navigateTo('/admin/notifications')">
        <BellIcon class="size-4" />
      </Button>
    </div>
  </header>
</template>
