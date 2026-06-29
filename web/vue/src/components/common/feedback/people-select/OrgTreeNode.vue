<script setup lang="ts">
/**
 * OrgTreeNode - 组织树节点组件
 *
 * 显示组织图标、名称、人员数量、展开按钮、三态复选框。
 * 支持懒加载指示器。
 */
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { Building2, ChevronRight, Loader2 } from '@lucide/vue'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/utils'
import type { FlatOrgNode } from './useOrgPeopleTree'

interface Props {
  /** 扁平化组织节点 */
  node: FlatOrgNode
  /** 是否显示复选框 */
  checkable?: boolean
  /** 是否禁用 */
  disabled?: boolean
  /** 自定义样式 */
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  checkable: true,
  disabled: false,
  class: undefined,
})

interface Emits {
  /** 切换展开状态 */
  (e: 'toggle-expand', id: string): void
  /** 切换选中状态 */
  (e: 'toggle-check', id: string): void
}

const emit = defineEmits<Emits>()

// 计算缩进样式
const indentStyle = {
  paddingLeft: `${props.node.tree_level * 20}px`,
}

// 计算复选框状态
const checkboxState = computed(() => {
  return props.node.checkState
})

// 是否正在加载
const isLoading = computed(() => {
  // 这里需要从父组件传入 loading 状态，暂时返回 false
  return false
})

// 是否有子节点
const hasChildren = computed(() => {
  return !props.node.tree_leaf && ((props.node.has_org_num ?? 0) > 0 || (props.node.has_user_num ?? 0) > 0)
})

// 处理展开按钮点击
function handleExpandClick(event: MouseEvent) {
  event.stopPropagation()
  if (!isLoading.value) {
    emit('toggle-expand', props.node.id)
  }
}

// 处理复选框点击
function handleCheckChange() {
  if (!props.disabled) {
    emit('toggle-check', props.node.id)
  }
}

// 获取复选框的选中状态
const isChecked = computed(() => props.node.checkState === 'checked')
const isIndeterminate = computed(() => props.node.checkState === 'indeterminate')
</script>

<template>
  <div
    :class="cn(
      'flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-muted/50 cursor-pointer',
      props.class
    )"
    :style="indentStyle"
  >
    <!-- 展开按钮 -->
    <button
      type="button"
      :class="cn(
        'flex h-5 w-5 items-center justify-center rounded-sm transition-transform',
        hasChildren ? 'hover:bg-muted' : 'invisible'
      )"
      :disabled="isLoading"
      @click="handleExpandClick"
    >
      <Loader2 v-if="isLoading" class="h-3.5 w-3.5 animate-spin text-muted-foreground" />
      <ChevronRight
        v-else-if="hasChildren"
        :class="cn(
          'h-4 w-4 text-muted-foreground transition-transform',
          node.expanded && 'rotate-90'
        )"
      />
    </button>

    <!-- 复选框 -->
    <Checkbox
      v-if="checkable"
      :checked="isChecked"
      :indeterminate="isIndeterminate"
      :disabled="disabled"
      @update:checked="handleCheckChange"
    />

    <!-- 组织图标 -->
    <Building2 class="h-4 w-4 text-muted-foreground shrink-0" />

    <!-- 组织名称 -->
    <span class="text-sm flex-1 truncate">{{ node.name }}</span>

    <!-- 人员数量 -->
    <span
      v-if="node.has_user_num !== undefined && node.has_user_num > 0"
      class="text-xs text-muted-foreground"
    >
      {{ node.has_user_num }}人
    </span>
  </div>
</template>
