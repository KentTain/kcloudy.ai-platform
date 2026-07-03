<script setup lang="ts">
import type { TreeSelectNode } from '@/framework/types/tree'
import type { HTMLAttributes } from 'vue'
import { ref, watch } from 'vue'
import { cn } from '@/lib/utils'
import { ChevronRight, ChevronDown, Loader2 } from '@lucide/vue'
import Checkbox from '@/components/ui/checkbox/Checkbox.vue'

/**
 * Tree 组件 Props
 * 支持基础展示、复选框选择、级联选择、异步加载等功能
 */
interface Props {
  /** 树形数据 */
  data: TreeSelectNode[]
  /** 默认展开层级 */
  defaultExpandLevel?: number
  /** 缩进距离（像素） */
  indent?: number
  /** 节点自定义类名 */
  nodeClass?: string
  /** 根容器类名 */
  class?: HTMLAttributes['class']
  /** 是否显示复选框 */
  checkable?: boolean
  /** 是否级联选择（父子联动） */
  cascade?: boolean
  /** 选中的节点 ID 列表（v-model） */
  modelValue?: (string | number)[]
  /** 是否多选模式 */
  multiple?: boolean
  /** 异步加载子节点 */
  loadData?: (node: TreeSelectNode, callback: (children: TreeSelectNode[]) => void) => void
  /** 是否显示连接线 */
  showLine?: boolean
  /** 是否禁用整棵树 */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultExpandLevel: 1,
  indent: 20,
  nodeClass: '',
  checkable: false,
  cascade: false,
  modelValue: () => [],
  multiple: false,
  showLine: false,
  disabled: false,
})

const emit = defineEmits<{
  'node-click': [{ node: TreeSelectNode; level: number }]
  'node-toggle': [{ node: TreeSelectNode; isExpanded: boolean }]
  'update:modelValue': [value: (string | number)[]]
}>()

// 展开的节点 ID 集合
const expandedKeys = ref<Set<string | number>>(new Set())
// 加载中的节点 ID 集合
const loadingKeys = ref<Set<string | number>>(new Set())
// 异步加载的子节点缓存
const loadedChildren = ref<Map<string | number, TreeSelectNode[]>>(new Map())

function isExpanded(nodeId: string | number): boolean {
  return expandedKeys.value.has(nodeId)
}

function isLoading(nodeId: string | number): boolean {
  return loadingKeys.value.has(nodeId)
}

function hasChildren(node: TreeSelectNode): boolean {
  // 检查原始 children 或已加载的 children
  if (node.children?.length) return true
  if (loadedChildren.value.has(node.id)) return true
  // 有 loadData 且未标记为叶子节点则可能有子节点
  if (props.loadData && node.isLeaf !== true) return true
  return false
}

function getChildren(node: TreeSelectNode): TreeSelectNode[] {
  // 优先使用异步加载的 children
  const asyncChildren = loadedChildren.value.get(node.id)
  if (asyncChildren) return asyncChildren
  return node.children ?? []
}

function toggleExpand(node: TreeSelectNode) {
  // 禁用状态下不响应
  if (props.disabled || node.disabled) return

  // 异步加载逻辑
  if (props.loadData && !node.children?.length && !loadedChildren.value.has(node.id) && node.isLeaf !== true) {
    loadingKeys.value.add(node.id)
    props.loadData(node, (children) => {
      loadingKeys.value.delete(node.id)
      loadedChildren.value.set(node.id, children)
      expandedKeys.value.add(node.id)
      emit('node-toggle', { node, isExpanded: true })
    })
    return
  }

  if (expandedKeys.value.has(node.id)) {
    expandedKeys.value.delete(node.id)
    emit('node-toggle', { node, isExpanded: false })
  } else {
    expandedKeys.value.add(node.id)
    emit('node-toggle', { node, isExpanded: true })
  }
}

function handleNodeClick(node: TreeSelectNode, level: number) {
  emit('node-click', { node, level })
}

// 检查节点是否选中
function isChecked(nodeId: string | number): boolean {
  return props.modelValue.includes(nodeId)
}

// 检查节点是否部分选中（用于级联模式）
function isIndeterminate(nodeId: string | number): boolean {
  if (!props.cascade || !props.checkable) return false

  const node = findNode(props.data, nodeId)
  if (!node) return false

  const children = getChildren(node)
  if (!children.length) return false

  const selectedChildren = children.filter(child => isChecked(child.id))
  if (selectedChildren.length === 0) return false
  if (selectedChildren.length === children.length) return false
  return true
}

// 查找节点
function findNode(nodes: TreeSelectNode[], id: string | number): TreeSelectNode | undefined {
  for (const node of nodes) {
    if (node.id === id) return node
    const found = findNode(getChildren(node), id)
    if (found) return found
  }
  return undefined
}

// 获取所有子节点 ID
function getAllDescendantIds(node: TreeSelectNode): (string | number)[] {
  const ids: (string | number)[] = []
  const children = getChildren(node)
  for (const child of children) {
    ids.push(child.id)
    ids.push(...getAllDescendantIds(child))
  }
  return ids
}

// 获取祖先节点
function getAncestorIds(nodes: TreeSelectNode[], targetId: string | number, path: (string | number)[] = []): (string | number)[] | null {
  for (const node of nodes) {
    if (node.id === targetId) return path
    const found = getAncestorIds(getChildren(node), targetId, [...path, node.id])
    if (found) return found
  }
  return null
}

// 检查节点的所有子节点是否都选中
function areAllChildrenSelected(node: TreeSelectNode): boolean {
  const children = getChildren(node)
  if (!children.length) return true
  return children.every(child => isChecked(child.id) && areAllChildrenSelected(child))
}

// 处理复选框点击
function handleCheck(node: TreeSelectNode) {
  if (props.disabled || node.disabled) return

  const currentChecked = isChecked(node.id)
  let newValues: (string | number)[]

  if (!props.cascade) {
    // 非级联模式：简单切换
    if (currentChecked) {
      newValues = props.modelValue.filter(id => id !== node.id)
    } else {
      if (!props.multiple) {
        newValues = [node.id]
      } else {
        newValues = [...props.modelValue, node.id]
      }
    }
  } else {
    // 级联模式：父子联动
    if (currentChecked) {
      // 取消选中：移除自己、所有子孙节点、祖先节点
      const descendantIds = getAllDescendantIds(node)
      const ancestorIds = getAncestorIds(props.data, node.id) ?? []
      newValues = props.modelValue.filter(id =>
        id !== node.id && !descendantIds.includes(id) && !ancestorIds.includes(id)
      )
    } else {
      // 选中：添加自己、所有子孙节点
      const descendantIds = getAllDescendantIds(node)
      newValues = [...new Set([...props.modelValue, node.id, ...descendantIds])]

      // 检查祖先节点是否需要选中
      const ancestorIds = getAncestorIds(props.data, node.id) ?? []
      for (const ancestorId of ancestorIds.reverse()) {
        const ancestor = findNode(props.data, ancestorId)
        if (ancestor && areAllChildrenSelected(ancestor)) {
          newValues.push(ancestorId)
        }
      }
      newValues = [...new Set(newValues)]
    }
  }

  emit('update:modelValue', newValues)
}

// 初始化默认展开层级
function initExpandedKeys(nodes: TreeSelectNode[], level: number = 0) {
  for (const node of nodes) {
    if (level < props.defaultExpandLevel && hasChildren(node)) {
      expandedKeys.value.add(node.id)
      initExpandedKeys(getChildren(node), level + 1)
    }
  }
}

watch(
  () => props.data,
  () => {
    if (props.defaultExpandLevel > 0) {
      expandedKeys.value.clear()
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
      :loading-keys="loadingKeys"
      :node-class="nodeClass"
      :is-expanded-fn="isExpanded"
      :is-loading-fn="isLoading"
      :has-children-fn="hasChildren"
      :get-children-fn="getChildren"
      :has-node-slot="!!$slots.node"
      :has-node-content-slot="!!$slots['node-content']"
      :checkable="checkable"
      :cascade="cascade"
      :disabled="disabled"
      :show-line="showLine"
      :is-checked-fn="isChecked"
      :is-indeterminate-fn="isIndeterminate"
      :on-check="handleCheck"
      :on-toggle-expand="toggleExpand"
      :on-node-click="handleNodeClick"
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

type NodeLocal = TreeSelectNode & {
  children?: NodeLocal[]
}

const TreeNode = defineComponent({
  name: 'TreeNode',
  props: {
    node: { type: Object as () => NodeLocal, required: true },
    level: { type: Number, default: 0 },
    indent: { type: Number, default: 20 },
    expandedKeys: { type: Object as () => Set<string | number>, required: true },
    loadingKeys: { type: Object as () => Set<string | number>, required: true },
    nodeClass: { type: String, default: '' },
    isExpandedFn: { type: Function, required: true },
    isLoadingFn: { type: Function, required: true },
    hasChildrenFn: { type: Function, required: true },
    getChildrenFn: { type: Function, required: true },
    hasNodeSlot: { type: Boolean, default: false },
    hasNodeContentSlot: { type: Boolean, default: false },
    checkable: { type: Boolean, default: false },
    cascade: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
    showLine: { type: Boolean, default: false },
    isCheckedFn: { type: Function, required: true },
    isIndeterminateFn: { type: Function, required: true },
    onCheck: { type: Function, required: true },
    onToggleExpand: { type: Function, required: true },
    onNodeClick: { type: Function, required: true },
  },
  setup(props, { slots }) {
    function handleToggleExpand(e: MouseEvent) {
      e.stopPropagation()
      props.onToggleExpand(props.node)
    }

    function handleCheckChange(checked: boolean) {
      props.onCheck(props.node)
    }

    function handleNodeClick() {
      props.onNodeClick(props.node, props.level)
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (): any => {
      const nodeIsExpanded = props.isExpandedFn(props.node.id)
      const nodeIsLoading = props.isLoadingFn(props.node.id)
      const nodeHasChildren = props.hasChildrenFn(props.node)
      const nodeIsDisabled = props.disabled || props.node.disabled
      const nodeIsChecked = props.isCheckedFn(props.node.id)
      const nodeIsIndeterminate = props.isIndeterminateFn(props.node.id)

      // 渲染子节点
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const childrenVNodes: any = nodeHasChildren && nodeIsExpanded
        ? props.getChildrenFn(props.node).map((child: NodeLocal): any =>
            h(TreeNode as any, {
              key: child.id,
              node: child,
              level: props.level + 1,
              indent: props.indent,
              expandedKeys: props.expandedKeys,
              loadingKeys: props.loadingKeys,
              nodeClass: props.nodeClass,
              isExpandedFn: props.isExpandedFn,
              isLoadingFn: props.isLoadingFn,
              hasChildrenFn: props.hasChildrenFn,
              getChildrenFn: props.getChildrenFn,
              hasNodeSlot: props.hasNodeSlot,
              hasNodeContentSlot: props.hasNodeContentSlot,
              checkable: props.checkable,
              cascade: props.cascade,
              disabled: props.disabled,
              showLine: props.showLine,
              isCheckedFn: props.isCheckedFn,
              isIndeterminateFn: props.isIndeterminateFn,
              onCheck: props.onCheck,
              onToggleExpand: props.onToggleExpand,
              onNodeClick: props.onNodeClick,
            })
          )
        : null

      // 计算缩进
      const paddingLeft = props.level * props.indent + 8

      // 渲染节点内容
      const nodeContent = props.hasNodeSlot
        ? slots.node?.({ node: props.node, level: props.level, isExpanded: nodeIsExpanded })
        : props.hasNodeContentSlot
          ? h('div', { class: 'flex items-center gap-2' }, [
              props.checkable
                ? h(Checkbox, {
                    checked: nodeIsChecked,
                    indeterminate: nodeIsIndeterminate,
                    disabled: nodeIsDisabled,
                    'onUpdate:checked': handleCheckChange,
                    onClick: (e: MouseEvent) => e.stopPropagation(),
                  })
                : null,
              h('span', { class: cn('flex h-4 w-4 items-center justify-center') },
                nodeHasChildren ? [h(nodeIsExpanded ? ChevronDown : ChevronRight, { class: 'h-3 w-3' })] : []
              ),
              slots.nodeContent?.({ node: props.node, level: props.level }),
            ])
          : h('div', { class: 'flex items-center gap-2' }, [
              props.checkable
                ? h(Checkbox, {
                    checked: nodeIsChecked,
                    indeterminate: nodeIsIndeterminate,
                    disabled: nodeIsDisabled,
                    'onUpdate:checked': handleCheckChange,
                    onClick: (e: MouseEvent) => e.stopPropagation(),
                  })
                : null,
              h('span', { class: 'text-sm' }, props.node.name),
            ])

      // 渲染展开/折叠按钮
      const expandButton = nodeHasChildren
        ? h('button', {
            type: 'button',
            class: cn(
              'flex h-4 w-4 items-center justify-center rounded hover:bg-muted',
              nodeIsDisabled && 'cursor-not-allowed opacity-50'
            ),
            disabled: nodeIsDisabled,
            onClick: handleToggleExpand,
          }, [
            nodeIsLoading
              ? h(Loader2, { class: 'h-3 w-3 animate-spin' })
              : h(nodeIsExpanded ? ChevronDown : ChevronRight, { class: 'h-3 w-3' }),
          ])
        : props.checkable
          ? null
          : h('span', { class: 'h-4 w-4' })

      // 连接线样式
      const lineStyle = props.showLine
        ? { borderLeft: '1px dashed var(--border)', marginLeft: `${props.indent / 2}px` }
        : {}

      return h('div', { class: 'flex flex-col' }, [
        h('div', {
          class: cn(
            'flex items-center gap-2 rounded-md px-2 py-1.5',
            !nodeIsDisabled && 'cursor-pointer hover:bg-muted/50',
            nodeIsDisabled && 'cursor-not-allowed opacity-50',
            props.nodeClass
          ),
          style: { paddingLeft: `${paddingLeft}px` },
          onClick: nodeIsDisabled ? undefined : handleNodeClick,
        }, [
          expandButton,
          nodeContent,
        ]),
        childrenVNodes && h('div', { style: lineStyle }, childrenVNodes),
      ])
    }
  },
})
</script>
