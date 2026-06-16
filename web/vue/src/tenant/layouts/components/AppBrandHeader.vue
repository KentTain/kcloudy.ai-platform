<script setup lang="ts">
/**
 * AppBrandHeader 品牌标识组件
 * 显示 Logo 图标和 "KCloudy / 管理后台" 文字
 * 支持 Sidebar collapsible="icon" 折叠模式（CSS 自动处理）
 * 点击可导航到管理后台首页
 */
import { Shield } from "@lucide/vue";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
</script>

<template>
  <SidebarMenu>
    <SidebarMenuItem>
      <SidebarMenuButton size="lg" as-child tooltip="KCloudy 管理后台">
        <router-link to="/admin">
          <div class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
            <Shield class="size-4" />
          </div>
          <div class="grid flex-1 text-left text-sm leading-tight">
            <span class="truncate font-medium">KCloudy</span>
            <span class="truncate text-xs">管理后台</span>
          </div>
        </router-link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  </SidebarMenu>
</template>
