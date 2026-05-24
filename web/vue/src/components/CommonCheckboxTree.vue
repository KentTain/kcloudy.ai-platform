<script setup lang="ts">
import type { TreeComponentNode } from '@/framework/types/tree'
import type { HTMLAttributes } from 'vue'
import { computed, ref } from 'vue'
import { cn } from '@/lib/utils'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Search } from '@lucide/vue'
import CommonTree from '@/components/CommonTree.vue'

interface Props {
  data: TreeComponentNode[]
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

const searchQuery = ref('')

// 判断节点是否为叶子节点
function isLeaf(node: TreeComponentNode): boolean {
  return !node.children?.length
}

// 获取节点的所有后代叶子节点 ID
function getDescendantLeafIds(node: TreeComponentNode): (string | number)[] {
  const leafIds: (string | number)[] = []
  function collect(n: TreeComponentNode) {
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
function getNodeCheckState(node: TreeComponentNode): 'checked' | 'unchecked' | 'indeterminate' {
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
function handleCheck(node: TreeComponentNode) {
  if (props.disabled) return

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

// 搜索过滤 - 计算可见节点
const filteredData = computed(() => {
  if (!searchQuery.value.trim()) return props.data

  const query = searchQuery.value.toLowerCase()
  const matchedIds = new Set<string | number>()
  const ancestorIds = new Set<string | number>()

  function findMatches(nodes: TreeComponentNode[], parentIds: (string | number)[] = []) {
    for (const node of nodes) {
      if (node.name.toLowerCase().includes(query)) {
        matchedIds.add(node.id)
        parentIds.forEach(id => ancestorIds.add(id))
      }
      if (node.children?.length) {
        findMatches(node.children, [...parentIds, node.id])
      }
    }
  }
  findMatches(props.data)

  function filterTree(nodes: TreeComponentNode[]): TreeComponentNode[] {
    return nodes
      .filter(node => matchedIds.has(node.id) || ancestorIds.has(node.id))
      .map(node => ({
        ...node,
        children: node.children ? filterTree(node.children) : undefined,
      }))
  }

  return filterTree(props.data)
})

const hasResults = computed(() => {
  if (!searchQuery.value.trim()) return true
  return filteredData.value.length > 0
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
    <CommonTree
      v-if="hasResults"
      :data="filteredData"
      :default-expand-level="defaultExpandLevel"
      :class="{ 'opacity-50 cursor-not-allowed': disabled }"
    >
      <template #node="{ node }">
        <div
          class="flex items-center gap-2"
          :class="{ 'cursor-not-allowed': disabled }"
          @click.stop="handleCheck(node as TreeComponentNode)"
        >
          <Checkbox
            :checked="getNodeCheckState(node as TreeComponentNode) === 'checked'"
            :indeterminate="getNodeCheckState(node as TreeComponentNode) === 'indeterminate'"
            :disabled="disabled"
          />
          <span
            class="text-sm"
            :class="cn(
              searchQuery && (node as TreeComponentNode).name.toLowerCase().includes(searchQuery.toLowerCase())
                && 'text-primary font-medium'
            )"
          >
            {{ (node as TreeComponentNode).name }}
          </span>
        </div>
      </template>
    </CommonTree>

    <!-- 无匹配结果 -->
    <div v-else class="py-4 text-center text-sm text-muted-foreground">
      无匹配结果
    </div>
  </div>
</template>