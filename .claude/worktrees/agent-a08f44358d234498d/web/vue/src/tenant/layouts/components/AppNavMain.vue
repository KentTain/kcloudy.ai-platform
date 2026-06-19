<script setup lang="ts">
/**
 * AppNavMain 管理员菜单组件
 * 从 useAdminMenuStore 获取动态菜单数据
 * 一级菜单显示为分组标签（不可点击），二级菜单作为可点击菜单项平铺
 */
import type { FunctionalComponent } from 'vue'
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as LucideIcons from '@lucide/vue'
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { useAdminMenuStore } from '@/tenant/stores/adminMenu'

/**
 * 默认图标（当指定图标不存在时使用）
 */
const DEFAULT_ICON = LucideIcons.Folder

/**
 * 获取图标组件
 * @param iconName 图标名称
 * @returns 图标组件或默认图标
 */
function getIconComponent(iconName: string | null | undefined): FunctionalComponent | undefined {
  if (!iconName) return undefined
  const icon = (LucideIcons as unknown as Record<string, FunctionalComponent>)[iconName]
  return icon || DEFAULT_ICON
}

const route = useRoute()
const router = useRouter()
const adminMenuStore = useAdminMenuStore()

/**
 * 判断菜单项是否为激活态
 */
const isItemActive = (path: string | undefined): boolean | undefined => {
  if (!path) return undefined
  return route.path === path
}

/**
 * 导航到指定路径
 */
const handleNavigate = (url: string) => {
  router.push(url)
}

/** 组件挂载时获取管理员菜单 */
onMounted(() => {
  if (adminMenuStore.adminMenus.length === 0) {
    adminMenuStore.fetchAdminMenus()
  }
})
</script>

<template>
  <!-- 加载状态 -->
  <div v-if="adminMenuStore.loading" class="p-4 text-center text-muted-foreground text-sm">
    加载菜单中...
  </div>

  <!-- 空状态 -->
  <div v-else-if="adminMenuStore.adminMenus.length === 0" class="p-4 text-center text-muted-foreground text-sm">
    暂无可用菜单
  </div>

  <!-- 一级菜单作为分组标签，二级菜单平铺 -->
  <template v-else>
    <SidebarGroup v-for="item in adminMenuStore.adminMenus" :key="item.id">
      <SidebarGroupLabel class="mb-3 h-5 text-gray-500">{{ item.name }}</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          <SidebarMenuItem v-for="child in item.children" :key="child.id">
            <SidebarMenuButton
              :tooltip="child.name"
              :is-active="isItemActive(child.path)"
              class="h-10 hover:bg-accent-foreground/5"
              :class="isItemActive(child.path) ? 'bg-white! text-primary!' : ''"
              @click="child.path && handleNavigate(child.path)"
            >
              <component :is="getIconComponent(child.icon)" v-if="child.icon" />
              <span>{{ child.name }}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  </template>
</template>
