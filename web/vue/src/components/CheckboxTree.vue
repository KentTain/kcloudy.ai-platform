<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, ref, watch } from 'vue'
import { cn } from '@/lib/utils'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { ChevronRight, ChevronDown, Search } from '@lucide/vue'

export interface TreeNode {
  id: string | number
  name: string
  children?: TreeNode[]
}

interface Props {
  data: TreeNode[]
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
const expandedKeys = ref<Set<string | number>>(new Set())

// 判断节点是否为叶子节点
function isLeaf(node: TreeNode): boolean {
  return !node.children?.length
}

// 获取节点的所有后代叶子节点 ID
function getDescendantLeafIds(node: TreeNode): (string | number)[] {
  const leafIds: (string | number)[] = []
  function collect(n: TreeNode) {
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
function getNodeCheckState(node: TreeNode): 'checked' | 'unchecked' | 'indeterminate' {
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
function handleCheck(node: TreeNode) {
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

// 切换节点展开状态
function toggleExpand(nodeId: string | number) {
  if (expandedKeys.value.has(nodeId)) {
    expandedKeys.value.delete(nodeId)
  } else {
    expandedKeys.value.add(nodeId)
  }
}

// 搜索过滤
const filteredNodeIds = computed(() => {
  if (!searchQuery.value.trim()) return null

  const query = searchQuery.value.toLowerCase()
  const matchedIds = new Set<string | number>()
  const ancestorIds = new Set<string | number>()

  function findMatches(nodes: TreeNode[], parentIds: (string | number)[] = []) {
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

  return { matchedIds, ancestorIds }
})

// 判断节点是否应该显示
function shouldShowNode(node: TreeNode): boolean {
  if (!filteredNodeIds.value) return true
  const { matchedIds, ancestorIds } = filteredNodeIds.value
  return matchedIds.has(node.id) || ancestorIds.has(node.id)
}

// 初始化默认展开层级
function initExpandedKeys(nodes: TreeNode[], level: number = 0) {
  for (const node of nodes) {
    if (level < props.defaultExpandLevel && node.children?.length) {
      expandedKeys.value.add(node.id)
      initExpandedKeys(node.children, level + 1)
    }
  }
}

watch(
  () => props.data,
  () => {
    if (props.defaultExpandLevel > 0) {
      initExpandedKeys(props.data)
    }
  },
  { immediate: true }
)
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
    <div class="flex flex-col gap-1">
      <template v-if="filteredNodeIds && filteredNodeIds.matchedIds.size === 0">
        <div class="py-4 text-center text-sm text-muted-foreground">
          无匹配结果
        </div>
      </template>
      <template v-else>
        <CheckboxTreeNode
          v-for="node in data"
          :key="node.id"
          :node="node"
          :expanded-keys="expandedKeys"
          :filtered-node-ids="filteredNodeIds"
          :disabled="disabled"
          :should-show-node="shouldShowNode"
          :get-node-check-state="getNodeCheckState"
          :is-leaf="isLeaf"
          @toggle-expand="toggleExpand"
          @check="handleCheck"
        />
      </template>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, h, computed as hComputed } from 'vue'

type TreeNodeLocal = {
  id: string | number
  name: string
  children?: TreeNodeLocal[]
}

type FilterResult = {
  matchedIds: Set<string | number>
  ancestorIds: Set<string | number>
} | null

const CheckboxTreeNode = defineComponent({
  name: 'CheckboxTreeNode',
  props: {
    node: { type: Object as () => TreeNodeLocal, required: true },
    expandedKeys: { type: Object as () => Set<string | number>, required: true },
    filteredNodeIds: { type: Object as () => FilterResult, default: null },
    disabled: { type: Boolean, default: false },
    level: { type: Number, default: 0 },
    shouldShowNode: { type: Function, required: true },
    getNodeCheckState: { type: Function, required: true },
    isLeaf: { type: Function, required: true },
  },
  emits: ['toggleExpand', 'check'],
  setup(props, { emit }) {
    const isExpanded = hComputed(() => props.expandedKeys.has(props.node.id))
    const checkState = hComputed(() => props.getNodeCheckState(props.node))
    const hasChildren = hComputed(() => !!props.node.children?.length)

    function handleToggleExpand() {
      emit('toggleExpand', props.node.id)
    }

    function handleCheck() {
      emit('check', props.node)
    }

    return () => {
      if (!props.shouldShowNode(props.node)) return h('div')

      const childrenVNodes = hasChildren.value && isExpanded.value
        ? props.node.children!.map((child: TreeNodeLocal): ReturnType<typeof h> =>
            h(CheckboxTreeNode as any, {
              key: child.id,
              node: child,
              expandedKeys: props.expandedKeys,
              filteredNodeIds: props.filteredNodeIds,
              disabled: props.disabled,
              level: props.level + 1,
              shouldShowNode: props.shouldShowNode,
              getNodeCheckState: props.getNodeCheckState,
              isLeaf: props.isLeaf,
              onToggleExpand: (id: string | number) => emit('toggleExpand', id),
              onCheck: (node: TreeNodeLocal) => emit('check', node),
            })
          )
        : null

      return h('div', { class: 'flex flex-col' }, [
        h('div', {
          class: cn(
            'flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50',
            props.disabled && 'cursor-not-allowed opacity-50'
          ),
          style: { paddingLeft: `${props.level * 20 + 8}px` },
        }, [
          hasChildren.value
            ? h('button', {
                type: 'button',
                class: 'flex h-4 w-4 items-center justify-center rounded hover:bg-muted',
                onClick: handleToggleExpand,
              }, [
                h(isExpanded.value ? ChevronDown : ChevronRight, { class: 'h-3 w-3' }),
              ])
            : h('span', { class: 'h-4 w-4' }),
          h(Checkbox, {
            checked: checkState.value === 'checked',
            indeterminate: checkState.value === 'indeterminate',
            disabled: props.disabled,
            onUpdateChecked: handleCheck,
          }),
          h('span', {
            class: cn(
              'text-sm',
              props.filteredNodeIds?.matchedIds.has(props.node.id) && 'text-primary font-medium'
            ),
          }, props.node.name),
        ]),
        childrenVNodes,
      ])
    }
  },
})
</script>