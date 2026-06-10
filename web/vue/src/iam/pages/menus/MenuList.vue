<script setup lang="ts">
/**
 * MenuList 菜单管理页面
 * 左侧菜单树 + 右侧菜单详情
 */
import { computed, onMounted, ref } from 'vue'
import { useMenuStore } from '@/iam/stores/menu'
import type { MenuTreeNode } from '@/iam/types'
import MenuTree from '@/iam/components/MenuTree.vue'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FolderOpen } from '@lucide/vue'

const menuStore = useMenuStore()

const selectedMenuId = ref<string | null>(null)
const expandedMenuIds = ref<string[]>([])

// 递归查找菜单节点
const findMenuById = (menuList: MenuTreeNode[], id: string): MenuTreeNode | null => {
  for (const menu of menuList) {
    if (menu.id === id) return menu
    if (menu.children?.length) {
      const found = findMenuById(menu.children, id)
      if (found) return found
    }
  }
  return null
}

// 当前选中的菜单对象
const selectedMenu = computed<MenuTreeNode | null>(() => {
  if (!selectedMenuId.value) return null
  return findMenuById(menuStore.menus, selectedMenuId.value)
})

// 处理菜单选中
const handleMenuSelect = (id: string | null) => {
  selectedMenuId.value = id
}

// 加载菜单数据
onMounted(async () => {
  await menuStore.fetchMenus()
  // 默认展开第一级
  expandedMenuIds.value = menuStore.menus.map(m => m.id)
})
</script>

<template>
  <AppPage title="菜单管理" description="查看系统菜单树结构与详细信息" variant="workbench">
    <div class="flex min-h-[calc(100svh-10rem)] gap-4">
      <!-- 左侧菜单树 -->
      <Card class="flex min-h-0 w-[320px] shrink-0 flex-col gap-0 overflow-hidden py-0">
        <MenuTree
          :menus="menuStore.menus"
          :selected-id="selectedMenuId"
          :expanded-ids="expandedMenuIds"
          :loading="menuStore.loading"
          @update:selected-id="handleMenuSelect"
        />
      </Card>

      <!-- 右侧菜单详情 -->
      <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
        <div v-if="selectedMenu" class="flex flex-1 flex-col">
          <div class="border-b px-5 py-4">
            <div class="flex items-center gap-3">
              <div class="font-medium">{{ selectedMenu.name }}</div>
              <Badge variant="secondary">
                {{ selectedMenu.module }}
              </Badge>
            </div>
            <div class="text-muted-foreground mt-1 text-xs">
              编码：{{ selectedMenu.code }}
            </div>
          </div>
          <div class="flex-1 overflow-auto px-5 py-5">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">菜单名称</div>
                <div class="mt-2 font-medium">{{ selectedMenu.name }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">菜单编码</div>
                <div class="mt-2 font-mono text-sm">{{ selectedMenu.code }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">路由路径</div>
                <div class="mt-2 font-mono text-sm">{{ selectedMenu.path }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">所属模块</div>
                <div class="mt-2">
                  <Badge variant="outline">
                    {{ selectedMenu.module }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">图标</div>
                <div class="mt-2 font-medium">{{ selectedMenu.icon || '未设置' }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">是否可见</div>
                <div class="mt-2">
                  <Badge :variant="selectedMenu.is_visible ? 'default' : 'secondary'">
                    {{ selectedMenu.is_visible ? '可见' : '隐藏' }}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- 未选中状态 -->
        <div v-else class="flex flex-1 flex-col items-center justify-center gap-4 py-12">
          <FolderOpen class="text-muted-foreground h-12 w-12" />
          <div class="text-center">
            <div class="font-medium">请选择菜单</div>
            <div class="text-muted-foreground mt-1 text-sm">从左侧树中选择一个菜单查看详情</div>
          </div>
        </div>
      </Card>
    </div>
  </AppPage>
</template>
