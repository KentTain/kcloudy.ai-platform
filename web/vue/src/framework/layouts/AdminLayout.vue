<script setup lang="ts">
/**
 * AdminLayout 后台管理布局组件
 * 左右结构：左侧侧边栏，右侧上下结构（顶部导航 + 内容区）
 */
import { onMounted } from "vue";
import { SidebarProvider, Sidebar, SidebarInset, SidebarContent, SidebarHeader } from "@/components/ui/sidebar";
import AppTenantSwitcher from "./components/AppTenantSwitcher.vue";
import AppNavMain from "./components/AppNavMain.vue";
import AppHeaderLeft from "./components/AppHeaderLeft.vue";
import AppHeaderSearchBox from "./components/AppHeaderSearchBox.vue";
import AppHeaderRight from "./components/AppHeaderRight.vue";
import AppMain from "./components/AppMain.vue";
import { useNotificationStore } from "@/framework/stores/notification";

const notificationStore = useNotificationStore();

onMounted(() => {
  // 初始化模拟通知数据
  notificationStore.initMockData();
});
</script>

<template>
  <SidebarProvider class="h-svh overflow-hidden">
    <!-- 左侧：侧边栏 -->
    <Sidebar collapsible="icon" variant="sidebar" class="border-r">
      <!-- 租户切换器 -->
      <SidebarHeader>
        <AppTenantSwitcher />
      </SidebarHeader>

      <!-- 菜单导航 -->
      <SidebarContent>
        <AppNavMain />
      </SidebarContent>
    </Sidebar>

    <!-- 右侧：上下结构 -->
    <SidebarInset class="overflow-hidden flex flex-col">
      <!-- 上半部分：顶部导航栏 -->
      <header class="flex items-center gap-4 px-5 h-14 bg-background border-b shrink-0">
        <AppHeaderLeft />
        <AppHeaderSearchBox />
        <AppHeaderRight />
      </header>

      <!-- 下半部分：内容区 -->
      <router-view />
    </SidebarInset>
  </SidebarProvider>
</template>
