<script setup lang="ts">
/**
 * MenuTree 菜单树组件
 * 以树形结构展示菜单数据，支持展开/折叠和选中高亮
 */
import { computed } from 'vue'
import { Tree } from '@/components/ui/tree'
import type { TreeNodeType } from '@/components/ui/tree'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { FolderOpen, FileText } from '@lucide/vue'
import type { MenuTreeNode } from '@/iam/types'

interface Props {
  menus: MenuTreeNode[]
  selectedId?: string | null
  expandedIds?: string[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedId: null,
  expandedIds: () => [],
  loading: false,
})

const emit = defineEmits<{
  'update:selectedId': [value: string | null]
  'update:expandedIds': [value: string[]]
}>()

// 将 MenuTreeNode 转换为 TreeNodeType
const convertToTreeNode = (menuList: MenuTreeNode[]): TreeNodeType[] => {
  return menuList.map(menu => ({
    value: menu.id,
    label: menu.name,
    children: menu.children?.length ? convertToTreeNode(menu.children) : [],
  }))
}

// 菜单树数据
const treeData = computed<TreeNodeType[]>(() => convertToTreeNode(props.menus))

// 选中的菜单节点值（用于 Tree 组件）
const selectedValues = computed<string[]>(() =>
  props.selectedId ? [props.selectedId] : [],
)

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
  if (!props.selectedId) return null
  return findMenuById(props.menus, props.selectedId)
})

// 处理树节点点击
const handleNodeClick = (node: TreeNodeType) => {
  emit('update:selectedId', node.value as string)
}
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="border-b px-4 py-4">
      <div class="font-medium">菜单树</div>
      <div class="text-muted-foreground mt-1 text-xs">点击菜单项查看详情</div>
    </div>
    <ScrollArea class="min-h-0 flex-1 px-3 py-3">
      <!-- 加载状态 -->
      <div v-if="loading" class="space-y-2 px-1">
        <Skeleton class="h-6 w-full" />
        <Skeleton class="h-6 w-4/5" />
        <Skeleton class="h-6 w-3/5" />
        <Skeleton class="ml-4 h-6 w-full" />
        <Skeleton class="ml-4 h-6 w-4/5" />
        <Skeleton class="h-6 w-full" />
      </div>
      <!-- 空状态 -->
      <div v-else-if="menus.length === 0" class="flex flex-col items-center justify-center gap-3 py-8">
        <FolderOpen class="text-muted-foreground h-10 w-10" />
        <div class="text-center">
          <div class="text-muted-foreground text-sm">暂无菜单数据</div>
        </div>
      </div>
      <!-- 菜单树 -->
      <Tree
        v-else
        :model-value="selectedValues"
        :data="treeData"
        :expanded-value="expandedIds"
        :multiple="false"
        :show-line="true"
        @on-node-click="handleNodeClick"
      >
        <template #leaf-icon>
          <FileText class="h-4 w-4 text-muted-foreground" />
        </template>
      </Tree>
    </ScrollArea>
    <!-- 选中菜单的模块标识 -->
    <div v-if="selectedMenu" class="border-t px-4 py-3">
      <div class="text-muted-foreground text-xs">所属模块</div>
      <div class="mt-1">
        <Badge variant="secondary">
          {{ selectedMenu.module }}
        </Badge>
      </div>
    </div>
  </div>
</template>
