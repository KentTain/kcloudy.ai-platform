<script setup lang="ts">
/**
 * PeopleSelectDialog — 人员选择器弹窗
 *
 * 弹窗封装：Dialog + PeopleSelectView + 确认/取消按钮
 */

import { ref, watch, computed } from "vue"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Button,
} from "@/components"
import PeopleSelectView from "./PeopleSelectView.vue"
import type { OrgTreeNode, PeopleItem } from "./types"

interface Props {
  /** 是否显示弹窗 */
  open: boolean
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的人员 ID 列表 */
  disabledIds?: string[]
  /** 已选中的人员 ID 列表 */
  modelValue?: string[]
  /** 弹窗标题 */
  title?: string
  /** 确认按钮文本 */
  confirmText?: string
  /** 加载组织子节点 API */
  loadOrgNodes: (parentId?: string) => Promise<OrgTreeNode[]>
  /** 搜索人员 API */
  searchPeople: (keyword: string) => Promise<PeopleItem[]>
  /** 加载组织下人员 API */
  loadOrgPeople: (orgId: string) => Promise<PeopleItem[]>
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  multiple: true,
  disabledIds: () => [],
  modelValue: () => [],
  title: "选择人员",
  confirmText: "确定",
})

const emit = defineEmits<{
  "update:open": [value: boolean]
  "update:modelValue": [value: string[]]
  confirm: [userIds: string[], users: PeopleItem[]]
  cancel: []
}>()

// 内部选中的数据
const selectedIds = ref<string[]>([...props.modelValue])
const selectedUsers = ref<PeopleItem[]>([])

// 重置选择（每次打开时重置为传入的 modelValue）
watch(
  () => props.open,
  (newVal) => {
    if (newVal) {
      selectedIds.value = [...props.modelValue]
    }
  }
)

// 处理选择变化
function handleSelect(people: PeopleItem[]) {
  selectedUsers.value = people
  selectedIds.value = people.map((p) => p.user_id)
}

// 确认
function handleConfirm() {
  emit("update:modelValue", selectedIds.value)
  emit("confirm", selectedIds.value, selectedUsers.value)
  emit("update:open", false)
}

// 取消
function handleCancel() {
  emit("cancel")
  emit("update:open", false)
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="max-w-[720px] p-0">
      <DialogHeader class="px-4 pt-4 pb-2">
        <DialogTitle>{{ title }}</DialogTitle>
      </DialogHeader>

      <div class="px-4 pb-2">
        <PeopleSelectView
          v-model="selectedIds"
          :multiple="multiple"
          :disabled-ids="disabledIds"
          :load-org-nodes="loadOrgNodes"
          :search-people="searchPeople"
          :load-org-people="loadOrgPeople"
          @select="handleSelect"
        />
      </div>

      <DialogFooter class="px-4 py-3 border-t">
        <Button variant="outline" @click="handleCancel">
          取消
        </Button>
        <Button @click="handleConfirm">
          {{ confirmText }}
          <template v-if="selectedIds.length > 0">
            ({{ selectedIds.length }})
          </template>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
