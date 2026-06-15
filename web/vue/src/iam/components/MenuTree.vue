<script setup lang="ts">
/**
 * MenuTree 菜单树组件
 * 以树形结构展示菜单数据，支持展开/折叠和选中高亮
 */
import { computed } from 'vue'
import { Tree } from '@/components/common/data-display/tree'
import type { TreeSelectNode } from '@/framework/types/tree'
import { useTreeData } from '@/framework/composables/useTreeData'
import { Badge, Skeleton } from '@/components'
import { ScrollArea } from '@/components/ui/scroll-area'
import { FolderOpen } from '@lucide/vue'
import type { MenuTreeNode } from '@/iam/types'
import { findMenuById } from '@/iam/utils/menu'

/** 扩展 TreeSelectNode 以包含 MenuTree 需要的 module 信息 */
interface MenuTreeSelectNode extends TreeSelectNode {
  module?: string
  code?: string
  path?: string
}

interface Props {
  menus: MenuTreeNode[]
  selectedId?: string | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedId: null,
  loading: false,
})

const emit = defineEmits<{
  'update:selectedId': [value: string | null]
}>()

// 使用 useTreeData composable 转换菜单数据
const { treeData, selectedIds } = useTreeData<MenuTreeNode, MenuTreeSelectNode>({
  source: () => props.menus,
  modelValue: () => props.selectedId ? [props.selectedId] : [],
  mode: 'single',
})

// 当前选中的菜单对象
const selectedMenu = computed<MenuTreeNode | null>(() => {
  if (!props.selectedId) return null
  return findMenuById(props.menus, props.selectedId)
})

// 处理树节点点击
const handleNodeClick = ({ node }: { node: MenuTreeSelectNode; level: number }) => {
  emit('update:selectedId', node.id as string)
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
        :data="treeData"
        :model-value="selectedIds"
        :multiple="false"
        :show-line="true"
        :default-expand-level="2"
        @node-click="handleNodeClick"
      >
        <template #label="{ node }">
          <div class="flex items-center gap-2">
            <span class="truncate">{{ node.name }}</span>
            <Badge
              v-if="(node as MenuTreeSelectNode).module"
              variant="outline"
              class="text-xs"
            >
              {{ (node as MenuTreeSelectNode).module }}
            </Badge>
          </div>
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
