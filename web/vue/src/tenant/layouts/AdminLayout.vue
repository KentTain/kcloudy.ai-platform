<script setup lang="ts">
/**
 * AdminLayout 管理后台布局组件
 * 左右结构：左侧侧边栏（支持折叠图标模式），右侧上下结构（顶部导航 + 内容区）
 */
import { computed } from "vue";
import { useRoute } from "vue-router";
import {
  SidebarProvider,
  Sidebar,
  SidebarInset,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import AppBrandHeader from "./components/AppBrandHeader.vue";
import AppNavMain from "./components/AppNavMain.vue";
import AppNavUser from "./components/AppNavUser.vue";

const route = useRoute();

const breadcrumbItems = computed(() => {
  const items: { title: string; url?: string }[] = [];
  const meta = route.meta;

  if (meta?.title) {
    items.push({ title: "管理后台", url: "/admin" });

    if (route.path !== "/admin") {
      items.push({ title: meta.title as string });
    }
  }

  return items;
});
</script>

<template>
  <SidebarProvider class="h-svh overflow-hidden">
    <!-- 左侧：侧边栏 -->
    <Sidebar collapsible="icon" variant="sidebar" class="border-r">
      <!-- 品牌标识 -->
      <SidebarHeader>
        <AppBrandHeader />
      </SidebarHeader>

      <!-- 菜单导航 -->
      <SidebarContent>
        <AppNavMain />
      </SidebarContent>

      <!-- 用户面板 -->
      <SidebarFooter>
        <AppNavUser />
      </SidebarFooter>
    </Sidebar>

    <!-- 右侧：上下结构 -->
    <SidebarInset class="flex flex-col">
      <!-- 顶部导航栏 -->
      <header class="flex items-center gap-2 px-4 h-14 shrink-0 border-b">
        <SidebarTrigger class="-ml-1" />
        <Separator orientation="vertical" class="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <template v-for="(item, index) in breadcrumbItems" :key="item.title">
              <BreadcrumbItem v-if="index < breadcrumbItems.length - 1">
                <BreadcrumbLink as-child>
                  <router-link :to="item.url || '#'">{{ item.title }}</router-link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator v-if="index < breadcrumbItems.length - 1" />
              <BreadcrumbItem v-if="index === breadcrumbItems.length - 1">
                <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
              </BreadcrumbItem>
            </template>
          </BreadcrumbList>
        </Breadcrumb>
      </header>

      <!-- 内容区 -->
      <div class="flex-1 flex flex-col overflow-hidden p-4">
        <router-view />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
