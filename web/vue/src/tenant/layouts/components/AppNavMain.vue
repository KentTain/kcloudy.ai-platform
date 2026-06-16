<script setup lang="ts">
/**
 * AppNavMain 管理员菜单组件
 * 从 useAdminMenuStore 获取动态菜单数据，支持平铺菜单和二级子菜单展开
 */
import type { FunctionalComponent } from 'vue'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as LucideIcons from '@lucide/vue'
import { ChevronRight } from '@lucide/vue'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from '@/components/ui/sidebar'
import { useAdminMenuStore, type AdminMenuItem } from '@/tenant/stores/adminMenu'

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
  const icon = (LucideIcons as Record<string, FunctionalComponent>)[iconName]
  return icon || DEFAULT_ICON
}

const route = useRoute()
const router = useRouter()
const adminMenuStore = useAdminMenuStore()

/** 手动展开的菜单项 ID 集合 */
const expandedMenus = ref<Set<string>>(new Set())

/**
 * 判断菜单项是否为激活态
 */
const isItemActive = (path: string | undefined): boolean | undefined => {
  if (!path) return undefined
  return route.path === path
}

/**
 * 判断菜单项是否有子菜单处于激活态
 */
const isSubActive = (item: AdminMenuItem): boolean =>
  item.children?.some((child) => child.path && route.path === child.path) ?? false

/**
 * 切换菜单项的展开/折叠
 */
const toggleExpand = (id: string) => {
  const newSet = new Set(expandedMenus.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  expandedMenus.value = newSet
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

  <!-- 菜单列表 -->
  <SidebarGroup v-else>
    <SidebarMenu>
      <template v-for="item in adminMenuStore.adminMenus" :key="item.id">
        <!-- 有子菜单的菜单项：使用 Collapsible 展开/折叠 -->
        <SidebarMenuItem v-if="item.children && item.children.length > 0">
          <Collapsible
            :open="expandedMenus.has(item.id) || isSubActive(item)"
            @update:open="toggleExpand(item.id)"
          >
            <CollapsibleTrigger as-child>
              <SidebarMenuButton
                :tooltip="item.name"
                class="h-10 hover:bg-accent-foreground/5"
              >
                <component :is="getIconComponent(item.icon)" v-if="item.icon" />
                <span>{{ item.name }}</span>
                <ChevronRight
                  class="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90"
                />
              </SidebarMenuButton>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem
                  v-for="child in item.children"
                  :key="child.id"
                >
                  <SidebarMenuSubButton
                    :is-active="isItemActive(child.path)"
                    @click="child.path && handleNavigate(child.path)"
                  >
                    <span>{{ child.name }}</span>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </Collapsible>
        </SidebarMenuItem>

        <!-- 无子菜单的菜单项：直接导航 -->
        <SidebarMenuItem v-else>
          <SidebarMenuButton
            :tooltip="item.name"
            :is-active="isItemActive(item.path)"
            class="h-10 hover:bg-accent-foreground/5"
            :class="isItemActive(item.path) ? 'bg-white! text-primary!' : ''"
            @click="item.path && handleNavigate(item.path)"
          >
            <component :is="getIconComponent(item.icon)" v-if="item.icon" />
            <span>{{ item.name }}</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </template>
    </SidebarMenu>
  </SidebarGroup>
</template>
