<script setup lang="ts">
import { computed } from "vue"
import { Pencil, ShieldOff, ShieldCheck, KeyRound, Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { User } from "@/iam/types"

const props = defineProps<{ row: User }>()

const emit = defineEmits<{
  edit: [row: User]
  disable: [row: User]
  enable: [row: User]
  resetPassword: [row: User]
  delete: [row: User]
}>()

const actions = computed<RowAction[]>(() => {
  const list: RowAction[] = [
    { key: "edit", label: "编辑", icon: Pencil, onClick: () => emit("edit", props.row) },
  ]
  if (props.row.status === "active") {
    list.push({ key: "disable", label: "停用", icon: ShieldOff, onClick: () => emit("disable", props.row) })
  } else {
    list.push({ key: "enable", label: "启用", icon: ShieldCheck, onClick: () => emit("enable", props.row) })
  }
  list.push({ key: "resetPassword", label: "重置密码", icon: KeyRound, onClick: () => emit("resetPassword", props.row) })
  list.push({ key: "delete", label: "删除", icon: Trash2, variant: "destructive", onClick: () => emit("delete", props.row) })
  return list
})
</script>

<template>
  <RowActions :actions="actions" />
</template>
