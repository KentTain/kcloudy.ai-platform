<script setup lang="ts">
/**
 * OrganizationSelectView - 组织选择视图
 *
 * 左右布局：左侧组织树 + 右侧已选组织列表
 * 使用 useOrgTree composable 和 OrgTreeNode 组件
 */

import { computed, watch, onMounted } from 'vue'
import { Search, X, Building2 } from '@lucide/vue'
import { Input, Badge, Skeleton, Button } from '@/components'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { OrganizationItem } from '../people-select/types'
import { useOrgTree } from './useOrgTree'
import OrgTreeNode from './OrgTreeNode.vue'

interface Props {
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的组织 ID 列表 */
  disabledIds?: string[]
  /** 已选中的组织 ID 列表（v-model） */
  modelValue?: string[]
  /** 默认展开层级 */
  defaultExpandLevel?: number
}

const props = withDefaults(defineProps<Props>(), {
  multiple: true,
  disabledIds: () => [],
  modelValue: () => [],
  defaultExpandLevel: 1,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  'select': [orgs: OrganizationItem[]]
}>()

// ========== Composable ==========

const {
  flatVisibleNodes,
  checkedIds,
  expandedIds,
  loading,
  searchKeyword,
  loadRoot,
  toggleExpand,
  toggleCheck,
  setSearchKeyword,
  clearSelection,
  getSelectedOrgs,
} = useOrgTree({
  multiple: props.multiple,
  cascade: true,
  modelValue: props.modelValue,
  disabledIds: props.disabledIds,
  defaultExpandLevel: props.defaultExpandLevel,
})

// ========== 已选组织 ==========

// 已选组织列表
const selectedOrgs = computed<OrganizationItem[]>(() => getSelectedOrgs())

// 监听选中变化
watch(checkedIds, () => {
  emit('update:modelValue', Array.from(checkedIds.value))
  emit('select', getSelectedOrgs())
}, { deep: true })

// ========== 事件处理 ==========

function handleToggleExpand(orgId: string) {
  toggleExpand(orgId)
}

function handleToggleCheck(orgId: string) {
  toggleCheck(orgId)
}

function handleRemoveSelected(orgId: string) {
  toggleCheck(orgId)
}

function handleClearAll() {
  clearSelection()
}

// 判断组织是否禁用
const disabledIdSet = computed(() => new Set(props.disabledIds))

// ========== 搜索处理 ==========

function handleSearch(keyword: string) {
  setSearchKeyword(keyword)
}

// ========== 初始化 ==========

onMounted(() => {
  loadRoot()
})
</script>

<template>
  <div class="flex h-[460px] border rounded-lg overflow-hidden">
    <!-- 左侧：组织树 -->
    <div class="w-1/2 border-r flex flex-col bg-muted/20">
      <!-- 搜索框 -->
      <div class="p-3 border-b">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            :model-value="searchKeyword"
            placeholder="搜索组织..."
            class="pl-9 h-9 text-sm"
            @update:model-value="handleSearch"
          />
        </div>
      </div>

      <!-- 树内容 -->
      <ScrollArea class="flex-1">
        <div class="p-2">
          <div v-if="loading" class="space-y-2">
            <Skeleton v-for="i in 5" :key="i" class="h-8 w-full" />
          </div>
          <div v-else-if="flatVisibleNodes.length === 0" class="py-8 text-center text-muted-foreground text-sm">
            暂无组织数据
          </div>
          <template v-else>
            <OrgTreeNode
              v-for="node in flatVisibleNodes"
              :key="node.id"
              :node="node"
              :checkable="true"
              :disabled="disabledIdSet.has(node.id)"
              :loading="!node.tree_leaf && !node.data.children?.length && expandedIds.has(node.id)"
              class="mb-1"
              @toggle-expand="handleToggleExpand"
              @toggle-check="handleToggleCheck"
            />
          </template>
        </div>
      </ScrollArea>
    </div>

    <!-- 右侧：已选组织 -->
    <div class="w-1/2 flex flex-col">
      <!-- 头部 -->
      <div class="flex items-center justify-between px-4 py-3 border-b">
        <span class="text-sm font-medium">
          已选组织
          <Badge v-if="selectedOrgs.length > 0" variant="secondary" class="ml-2">
            {{ selectedOrgs.length }}
          </Badge>
        </span>
        <Button
          v-if="selectedOrgs.length > 0"
          variant="ghost"
          size="sm"
          class="h-7 px-2 text-xs text-muted-foreground"
          @click="handleClearAll"
        >
          清空
        </Button>
      </div>

      <!-- 已选列表 -->
      <ScrollArea class="flex-1">
        <div v-if="selectedOrgs.length === 0" class="flex flex-col items-center justify-center h-full text-muted-foreground">
          <Building2 class="h-12 w-12 mb-3 opacity-40" />
          <p class="text-sm">暂无选中组织</p>
        </div>
        <div v-else class="p-2">
          <div
            v-for="org in selectedOrgs"
            :key="org.id"
            class="flex items-center gap-3 px-3 py-2 mb-1 rounded-md hover:bg-muted/50 group"
          >
            <Building2 class="h-5 w-5 text-muted-foreground shrink-0" />
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">
                {{ org.name }}
              </div>
              <div v-if="org.tree_names" class="text-xs text-muted-foreground truncate">
                {{ org.tree_names }}
              </div>
            </div>
            <button
              type="button"
              class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-muted rounded"
              @click="handleRemoveSelected(org.id)"
            >
              <X class="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
