<script setup lang="ts">
/**
 * UserTreeNode - 用户树节点组件
 *
 * 显示头像、名称、组织路径、复选框。
 */
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { Checkbox } from '@/components'
import { cn } from '@/lib/utils'
import type { FlatOrgNode } from './useOrgPeopleTree'
import type { UserItem } from './types'
import PeopleAvatar from './PeopleAvatar.vue'

interface Props {
  /** 扁平化用户节点 */
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
  /** 切换选中状态 */
  (e: 'toggle-check', id: string): void
}

const emit = defineEmits<Emits>()

// 计算缩进样式
const indentStyle = {
  paddingLeft: `${props.node.tree_level * 20}px`,
}

// 获取用户数据
const userData = computed(() => {
  return props.node.data as UserItem
})

// 是否选中
const isChecked = computed(() => {
  return props.node.checkState === 'checked'
})

// 组织路径
const orgPath = computed(() => {
  return userData.value.org_tree_names || ''
})

// 处理复选框点击
function handleCheckChange() {
  if (!props.disabled) {
    emit('toggle-check', props.node.id)
  }
}
</script>

<template>
  <div
    :class="cn(
      'flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-muted/50',
      disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
      props.class
    )"
    :style="indentStyle"
  >
    <!-- 展开按钮占位 -->
    <div class="h-5 w-5" />

    <!-- 复选框 -->
    <Checkbox
      v-if="checkable"
      :checked="isChecked"
      :disabled="disabled"
      @update:checked="handleCheckChange"
    />

    <!-- 头像 -->
    <PeopleAvatar
      :id="userData.id"
      :username="userData.username"
      :avatar="userData.avatar"
      size="sm"
      class="shrink-0"
    />

    <!-- 用户信息 -->
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">
        {{ userData.nickname || userData.username }}
      </div>
      <div v-if="orgPath" class="text-xs text-muted-foreground truncate">
        {{ orgPath }}
      </div>
    </div>
  </div>
</template>
