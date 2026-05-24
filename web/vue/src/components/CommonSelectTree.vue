<script setup lang="ts">
import type { TreeComponentNode } from '@/framework/types/tree'
import type { HTMLAttributes } from 'vue'
import { ref, computed, watch } from 'vue'
import { cn } from '@/lib/utils'
import { ChevronDown, X } from '@lucide/vue'
import CommonTree from '@/components/CommonTree.vue'

interface Props {
  data: TreeComponentNode[]
  modelValue?: string | string[]
  mode?: 'single' | 'multiple'
  placeholder?: string
  disabled?: boolean
  defaultExpandLevel?: number
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  mode: 'single',
  placeholder: '请选择',
  disabled: false,
  defaultExpandLevel: 2,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
}>()

const isOpen = ref(false)
const selectedNode = ref<TreeComponentNode | null>(null)
const selectedNodes = ref<TreeComponentNode[]>([])

// 计算显示文本
const displayText = computed(() => {
  if (props.mode === 'single') {
    return selectedNode.value?.name ?? ''
  }
  return selectedNodes.value.map(n => n.name).join(', ')
})

function handleNodeClick({ node }: { node: TreeComponentNode; level: number }) {
  if (props.disabled) return

  if (props.mode === 'single') {
    selectedNode.value = node
    emit('update:modelValue', String(node.id))
    isOpen.value = false
  } else {
    const id = String(node.id)
    const currentValues = Array.isArray(props.modelValue) ? props.modelValue : []
    if (currentValues.includes(id)) {
      selectedNodes.value = selectedNodes.value.filter(n => String(n.id) !== id)
      emit('update:modelValue', currentValues.filter(v => v !== id))
    } else {
      selectedNodes.value.push(node)
      emit('update:modelValue', [...currentValues, id])
    }
  }
}

function toggleDropdown() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

function clearSelection() {
  selectedNode.value = null
  selectedNodes.value = []
  emit('update:modelValue', props.mode === 'single' ? '' : [])
}

// 同步外部 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (props.mode === 'single') {
      // 单选模式：根据 ID 查找节点
      const id = typeof newVal === 'string' ? newVal : ''
      if (id && (!selectedNode.value || String(selectedNode.value.id) !== id)) {
        // 在 data 中查找节点
        const findNode = (nodes: TreeComponentNode[]): TreeComponentNode | null => {
          for (const node of nodes) {
            if (String(node.id) === id) return node
            if (node.children) {
              const found = findNode(node.children)
              if (found) return found
            }
          }
          return null
        }
        selectedNode.value = findNode(props.data)
      } else if (!id) {
        selectedNode.value = null
      }
    } else {
      // 多选模式：根据 ID 数组更新选中节点
      const ids = Array.isArray(newVal) ? newVal : []
      // 简单同步：清空并重新添加（完整实现需要更复杂的 diff）
      if (ids.length === 0) {
        selectedNodes.value = []
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <div :class="cn('relative', props.class)">
    <!-- 输入框 -->
    <div
      :class="cn(
        'flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm cursor-pointer',
        isOpen && 'ring-2 ring-primary ring-offset-1',
        disabled && 'cursor-not-allowed opacity-50 bg-muted'
      )"
      @click="toggleDropdown"
    >
      <span :class="cn('flex-1', !displayText && 'text-muted-foreground')">
        {{ displayText || placeholder }}
      </span>
      <button
        v-if="displayText && !disabled"
        type="button"
        class="flex h-4 w-4 items-center justify-center rounded hover:bg-muted"
        @click.stop="clearSelection"
      >
        <X class="h-3 w-3" />
      </button>
      <ChevronDown class="h-4 w-4 text-muted-foreground" />
    </div>

    <!-- 下拉树面板 -->
    <div
      v-if="isOpen"
      class="absolute top-full left-0 z-50 mt-1 w-full rounded-md border border-border bg-white shadow-lg p-2 max-h-64 overflow-auto"
    >
      <CommonTree
        :data="data"
        :default-expand-level="defaultExpandLevel"
        @node-click="handleNodeClick"
      >
        <template #node-content="{ node }">
          <span
            class="text-sm"
            :class="cn(
              mode === 'single' && selectedNode?.id === node.id && 'text-primary font-medium',
              mode === 'multiple' && Array.isArray(modelValue) && modelValue.includes(String(node.id)) && 'text-primary font-medium'
            )"
          >
            {{ node.name }}
          </span>
        </template>
      </CommonTree>
    </div>
  </div>
</template>