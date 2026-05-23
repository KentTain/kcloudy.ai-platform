<script setup lang="ts">
/**
 * AdminLayout 后台管理布局组件
 */
import { SidebarProvider, Sidebar, SidebarInset, SidebarHeader, SidebarContent, SidebarFooter } from "@/components/ui/sidebar";
import { ChevronRight } from "@lucide/vue";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import AppNavMain from "./components/AppNavMain.vue";
import AppNavbar from "./components/AppNavbar.vue";
import AppMain from "./components/AppMain.vue";
import { useUserStore } from "@/framework/stores";

const userStore = useUserStore();
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
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <button class="flex w-full items-center gap-2 rounded-md p-2 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
              <Avatar class="h-8 w-8">
                <AvatarFallback class="bg-primary text-primary-foreground text-xs">
                  {{ userStore.userInfo?.nickname?.charAt(0) || "U" }}
                </AvatarFallback>
              </Avatar>
              <div class="flex flex-1 flex-col items-start gap-0.5 overflow-hidden group-data-[collapsible=icon]:hidden">
                <span class="text-sm font-medium truncate">{{ userStore.userInfo?.nickname || "用户" }}</span>
                <span class="text-xs text-muted-foreground truncate">{{ userStore.userInfo?.email || "" }}</span>
              </div>
              <ChevronRight class="ml-auto size-4 group-data-[collapsible=icon]:hidden" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" class="w-[--reka-dropdown-menu-trigger-width] min-w-48">
            <DropdownMenuItem @click="userStore.logout()">
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
    <SidebarInset>
      <AppNavbar />
      <AppMain />
    </SidebarInset>
  </SidebarProvider>
</template>
