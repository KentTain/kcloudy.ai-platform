<script setup lang="ts">
/**
 * AdminLayout 后台管理布局组件
 */
import { SidebarProvider, Sidebar, SidebarInset, SidebarHeader, SidebarContent, SidebarFooter } from "@/components/ui/sidebar";
import AppNavMain from "./components/AppNavMain.vue";
import AppNavbar from "./components/AppNavbar.vue";
import AppMain from "./components/AppMain.vue";
import AppSidebarFooter from "./components/AppSidebarFooter.vue";
import CommandPalette from "@/framework/components/CommandPalette.vue";
</script>

<template>
  <SidebarProvider class="h-svh overflow-hidden">
    <Sidebar collapsible="icon" variant="inset">
      <SidebarHeader>
        <div class="flex items-center gap-2 px-2 py-1">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
            AI
          </div>
          <span class="font-semibold text-sm group-data-[collapsible=icon]:hidden">AI 助手平台</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <AppNavMain />
      </SidebarContent>
      <SidebarFooter>
        <AppSidebarFooter />
      </SidebarFooter>
    </Sidebar>
    <SidebarInset>
      <AppNavbar />
      <AppMain />
    </SidebarInset>
  </SidebarProvider>
  <CommandPalette />
</template>
