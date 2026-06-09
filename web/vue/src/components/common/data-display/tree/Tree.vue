<script setup lang="ts">
import type { TreeComponentNode } from '@/framework/types/tree'
import type { HTMLAttributes } from 'vue'
import { ref, watch } from 'vue'
import { cn } from '@/lib/utils'
import { ChevronRight, ChevronDown } from '@lucide/vue'

interface Props {
  data: TreeComponentNode[]
  defaultExpandLevel?: number
  indent?: number
  nodeClass?: string
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  defaultExpandLevel: 1,
  indent: 20,
  nodeClass: '',
})

const emit = defineEmits<{
  'node-click': [{ node: TreeComponentNode; level: number }]
  'node-toggle': [{ node: TreeComponentNode; isExpanded: boolean }]
}>()

const expandedKeys = ref<Set<string | number>>(new Set())

function isExpanded(nodeId: string | number): boolean {
  return expandedKeys.value.has(nodeId)
}

function hasChildren(node: TreeComponentNode): boolean {
  return !!node.children?.length
}

function toggleExpand(node: TreeComponentNode) {
  if (expandedKeys.value.has(node.id)) {
    expandedKeys.value.delete(node.id)
  } else {
    expandedKeys.value.add(node.id)
  }
  emit('node-toggle', { node, isExpanded: isExpanded(node.id) })
}

function handleNodeClick(node: TreeComponentNode, level: number) {
  emit('node-click', { node, level })
}

// 初始化默认展开层级
function initExpandedKeys(nodes: TreeComponentNode[], level: number = 0) {
  for (const node of nodes) {
    if (level < props.defaultExpandLevel && hasChildren(node)) {
      expandedKeys.value.add(node.id)
      initExpandedKeys(node.children ?? [], level + 1)
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
  <div :class="cn('flex flex-col gap-1', props.class)">
    <TreeNode
      v-for="node in data"
      :key="node.id"
      :node="node"
      :level="0"
      :indent="indent"
      :expanded-keys="expandedKeys"
      :node-class="nodeClass"
      :is-expanded-fn="isExpanded"
      :has-children-fn="hasChildren"
      :has-node-slot="!!$slots.node"
      :has-node-content-slot="!!$slots.nodeContent"
      @toggle-expand="toggleExpand"
      @node-click="handleNodeClick"
    >
      <template #node="slotProps">
        <slot name="node" v-bind="slotProps" />
      </template>
      <template #node-content="slotProps">
        <slot name="node-content" v-bind="slotProps" />
      </template>
    </TreeNode>
  </div>
</template>

<script lang="ts">
import { defineComponent, h } from 'vue'

type NodeLocal = {
  id: string | number
  name: string
  children?: NodeLocal[]
  [key: string]: any
}

const TreeNode = defineComponent({
  name: 'TreeNode',
  props: {
    node: { type: Object as () => NodeLocal, required: true },
    level: { type: Number, default: 0 },
    indent: { type: Number, default: 20 },
    expandedKeys: { type: Object as () => Set<string | number>, required: true },
    nodeClass: { type: String, default: '' },
    isExpandedFn: { type: Function, required: true },
    hasChildrenFn: { type: Function, required: true },
    hasNodeSlot: { type: Boolean, default: false },
    hasNodeContentSlot: { type: Boolean, default: false },
  },
  emits: ['toggleExpand', 'nodeClick'],
  setup(props, { emit, slots }) {
    function handleToggleExpand() {
      emit('toggleExpand', props.node)
    }

    function handleNodeClick() {
      emit('nodeClick', props.node, props.level)
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (): any => {
      const nodeIsExpanded = props.isExpandedFn(props.node.id)
      const nodeHasChildren = props.hasChildrenFn(props.node)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const childrenVNodes: any = nodeHasChildren && nodeIsExpanded
        ? props.node.children!.map((child: NodeLocal): any =>
            h(TreeNode as any, {
              key: child.id,
              node: child,
              level: props.level + 1,
              indent: props.indent,
              expandedKeys: props.expandedKeys,
              nodeClass: props.nodeClass,
              isExpandedFn: props.isExpandedFn,
              hasChildrenFn: props.hasChildrenFn,
              hasNodeSlot: props.hasNodeSlot,
              hasNodeContentSlot: props.hasNodeContentSlot,
              onToggleExpand: (node: NodeLocal) => emit('toggleExpand', node),
              onNodeClick: (node: NodeLocal, level: number) => emit('nodeClick', node, level),
            })
          )
        : null

      // 只有父组件明确提供了 slot 才使用，否则显示默认内容
      const nodeContent = props.hasNodeSlot
        ? slots.node?.({ node: props.node, level: props.level, isExpanded: nodeIsExpanded })
        : props.hasNodeContentSlot
          ? h('div', { class: 'flex items-center gap-2' }, [
              h('span', { class: cn('flex h-4 w-4 items-center justify-center') },
                nodeHasChildren ? [h(nodeIsExpanded ? ChevronDown : ChevronRight, { class: 'h-3 w-3' })] : []
              ),
              slots.nodeContent?.({ node: props.node, level: props.level }),
            ])
          : h('span', { class: 'text-sm' }, props.node.name)

      return h('div', { class: 'flex flex-col' }, [
        h('div', {
          class: cn(
            'flex items-center gap-2 rounded-md px-2 py-1.5 cursor-pointer hover:bg-muted/50',
            props.nodeClass
          ),
          style: { paddingLeft: `${props.level * props.indent + 8}px` },
          onClick: handleNodeClick,
        }, [
          // 展开/折叠按钮（仅当 hasNodeSlot 为 false 时在此显示）
          !props.hasNodeSlot && nodeHasChildren
            ? h('button', {
                type: 'button',
                class: 'flex h-4 w-4 items-center justify-center rounded hover:bg-muted',
                onClick: (e: MouseEvent) => { e.stopPropagation(); handleToggleExpand() },
              }, [
                h(nodeIsExpanded ? ChevronDown : ChevronRight, { class: 'h-3 w-3' }),
              ])
            : !props.hasNodeSlot ? h('span', { class: 'h-4 w-4' }) : null,
          nodeContent,
        ]),
        childrenVNodes,
      ])
    }
  },
})
</script>
