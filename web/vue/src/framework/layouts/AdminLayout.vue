<script setup lang="ts">
/**
 * AdminLayout 后台管理布局组件
 * 左右结构：左侧侧边栏，右侧上下结构（顶部导航 + 内容区）
 */
import { onMounted } from "vue";
import { SidebarProvider, Sidebar, SidebarInset, SidebarContent } from "@/components/ui/sidebar";
import AppTenantSwitcher from "./components/AppTenantSwitcher.vue";
import AppNavMain from "./components/AppNavMain.vue";
import AppSearchBox from "./components/AppSearchBox.vue";
import AppHeaderRight from "./components/AppHeaderRight.vue";
import AppContentHeader from "./components/AppContentHeader.vue";
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
      <AppTenantSwitcher />

      <!-- 菜单导航 -->
      <SidebarContent>
        <AppNavMain />
      </SidebarContent>
    </Sidebar>

    <!-- 右侧：上下结构 -->
    <SidebarInset class="flex flex-col">
      <!-- 上半部分：顶部导航栏 -->
      <header class="flex items-center gap-4 px-5 h-14 bg-background border-b shrink-0">
        <AppSearchBox />
        <AppHeaderRight />
      </header>

      <!-- 下半部分：内容区 -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- 内容页导航栏 -->
        <AppContentHeader />

        <!-- 内容页 -->
        <AppMain />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
