<script setup lang="ts">
import type { TreeSelectNode } from '@/framework/types/tree'
import type { HTMLAttributes } from 'vue'
import { computed, ref, toRef } from 'vue'
import { cn } from '@/lib/utils'
import { useTreeData } from '@/framework/composables/useTreeData'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Search } from '@lucide/vue'
import Tree from './Tree.vue'

interface Props {
  data: TreeSelectNode[]
  modelValue?: (string | number)[]
  disabled?: boolean
  defaultExpandLevel?: number
  searchable?: boolean
  placeholder?: string
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  disabled: false,
  defaultExpandLevel: 1,
  searchable: true,
  placeholder: '搜索...',
})

const emit = defineEmits<{
  'update:modelValue': [value: (string | number)[]]
}>()

// 搜索关键词
const searchQuery = ref('')

// 使用 useTreeData 管理树数据
const { filteredData, treeData } = useTreeData<TreeSelectNode>({
  source: toRef(() => props.data),
  searchable: props.searchable,
  searchQuery,
  defaultExpandLevel: props.defaultExpandLevel,
})

// 判断节点是否为叶子节点
function isLeaf(node: TreeSelectNode): boolean {
  // 优先使用 isLeaf 字段，否则根据 children 判断
  if (node.isLeaf !== undefined) return node.isLeaf
  return !node.children?.length
}

// 获取节点的所有后代叶子节点 ID
function getDescendantLeafIds(node: TreeSelectNode): (string | number)[] {
  const leafIds: (string | number)[] = []
  function collect(n: TreeSelectNode) {
    if (isLeaf(n)) {
      leafIds.push(n.id)
    } else if (n.children) {
      n.children.forEach(collect)
    }
  }
  collect(node)
  return leafIds
}

// 计算节点的选中状态
function getNodeCheckState(node: TreeSelectNode): 'checked' | 'unchecked' | 'indeterminate' {
  if (isLeaf(node)) {
    return props.modelValue.includes(node.id) ? 'checked' : 'unchecked'
  }

  const descendantLeafIds = getDescendantLeafIds(node)
  if (descendantLeafIds.length === 0) return 'unchecked'

  const selectedCount = descendantLeafIds.filter(id => props.modelValue.includes(id)).length

  if (selectedCount === 0) return 'unchecked'
  if (selectedCount === descendantLeafIds.length) return 'checked'
  return 'indeterminate'
}

// 处理节点勾选
function handleCheck(node: TreeSelectNode) {
  if (props.disabled || node.disabled) return

  const currentState = getNodeCheckState(node)
  let newSelectedIds = [...props.modelValue]

  if (isLeaf(node)) {
    if (currentState === 'checked') {
      newSelectedIds = newSelectedIds.filter(id => id !== node.id)
    } else {
      newSelectedIds.push(node.id)
    }
  } else {
    const descendantLeafIds = getDescendantLeafIds(node)
    if (currentState === 'checked') {
      newSelectedIds = newSelectedIds.filter(id => !descendantLeafIds.includes(id))
    } else {
      for (const id of descendantLeafIds) {
        if (!newSelectedIds.includes(id)) {
          newSelectedIds.push(id)
        }
      }
    }
  }

  emit('update:modelValue', newSelectedIds)
}

// 是否有搜索结果
const hasResults = computed(() => {
  if (!props.searchable || !searchQuery.value.trim()) return true
  return filteredData.value.length > 0
})

// 获取要显示的树数据
const displayData = computed(() => {
  if (!props.searchable) return treeData.value
  return filteredData.value
})
</script>

<template>
  <div :class="cn('flex flex-col gap-2', props.class)">
    <!-- 搜索框 -->
    <div v-if="searchable" class="relative">
      <Search class="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        v-model="searchQuery"
        :placeholder="placeholder"
        :disabled="disabled"
        class="pl-8"
      />
    </div>

    <!-- 树结构 -->
    <Tree
      v-if="hasResults"
      :data="displayData"
      :default-expand-level="defaultExpandLevel"
      :class="{ 'opacity-50 cursor-not-allowed': disabled }"
    >
      <template #node="{ node }">
        <div
          class="flex items-center gap-2"
          :class="{ 'cursor-not-allowed': disabled || (node as TreeSelectNode).disabled }"
          @click.stop="handleCheck(node as TreeSelectNode)"
        >
          <Checkbox
            :checked="getNodeCheckState(node as TreeSelectNode) === 'checked'"
            :indeterminate="getNodeCheckState(node as TreeSelectNode) === 'indeterminate'"
            :disabled="disabled || (node as TreeSelectNode).disabled"
          />
          <span
            class="text-sm"
            :class="cn(
              searchQuery && (node as TreeSelectNode).name.toLowerCase().includes(searchQuery.toLowerCase())
                && 'text-primary font-medium'
            )"
          >
            {{ (node as TreeSelectNode).name }}
          </span>
        </div>
      </template>
    </Tree>

    <!-- 无匹配结果 -->
    <div v-else class="py-4 text-center text-sm text-muted-foreground">
      无匹配结果
    </div>
  </div>
</template>
