<script setup lang="ts">
/**
 * OrganizationSelectDialog - 组织选择器弹窗
 *
 * 弹窗封装：Dialog + OrganizationSelectView + 确认/取消按钮
 */

import { ref, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Button,
} from '@/components'
import { cn } from '@/lib/utils'
import type { OrganizationItem } from '../people-select/types'
import OrganizationSelectView from './OrganizationSelectView.vue'

interface Props {
  /** 是否显示弹窗 */
  open: boolean
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的组织 ID 列表 */
  disabledIds?: string[]
  /** 已选中的组织 ID 列表（v-model） */
  modelValue?: string[]
  /** 弹窗标题 */
  title?: string
  /** 确认按钮文本 */
  confirmText?: string
  /** 默认展开层级 */
  defaultExpandLevel?: number
  /** 弹窗大小 */
  size?: 'md' | 'lg' | 'xl'
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  multiple: true,
  disabledIds: () => [],
  modelValue: () => [],
  title: '选择组织',
  confirmText: '确定',
  defaultExpandLevel: 1,
  size: 'lg',
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  'update:modelValue': [value: string[]]
  'confirm': [orgIds: string[], orgs: OrganizationItem[]]
  'cancel': []
}>()

// 内部选中的数据
const internalSelectedIds = ref<string[]>([...props.modelValue])
const internalSelectedOrgs = ref<OrganizationItem[]>([])

// 弹窗打开时重置选择
watch(
  () => props.open,
  (newVal) => {
    if (newVal) {
      internalSelectedIds.value = [...props.modelValue]
    }
  }
)

// 同步外部 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (props.open) {
      internalSelectedIds.value = [...newVal]
    }
  }
)

// 处理选择变化
function handleSelect(orgs: OrganizationItem[]) {
  internalSelectedOrgs.value = orgs
}

function handleUpdateModelValue(ids: string[]) {
  internalSelectedIds.value = ids
}

// 确认
function handleConfirm() {
  emit('update:modelValue', internalSelectedIds.value)
  emit('confirm', internalSelectedIds.value, internalSelectedOrgs.value)
  emit('update:open', false)
}

// 取消
function handleCancel() {
  emit('cancel')
  emit('update:open', false)
}

// 弹窗大小映射
const sizeClasses: Record<string, string> = {
  md: 'sm:max-w-[600px]',
  lg: 'sm:max-w-[800px]',
  xl: 'sm:max-w-[1000px]',
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent
      :class="cn(sizeClasses[size], 'p-0 gap-0')"
      :show-close-button="true"
    >
      <DialogHeader class="px-5 pt-5 pb-3">
        <DialogTitle>{{ title }}</DialogTitle>
      </DialogHeader>

      <div class="px-5 pb-3">
        <OrganizationSelectView
          v-model="internalSelectedIds"
          :multiple="multiple"
          :disabled-ids="disabledIds"
          :default-expand-level="defaultExpandLevel"
          @select="handleSelect"
          @update:model-value="handleUpdateModelValue"
        />
      </div>

      <DialogFooter class="px-5 py-4 border-t bg-muted/30">
        <Button variant="outline" @click="handleCancel">
          取消
        </Button>
        <Button @click="handleConfirm">
          {{ confirmText }}
          <template v-if="internalSelectedIds.length > 0">
            ({{ internalSelectedIds.length }})
          </template>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
