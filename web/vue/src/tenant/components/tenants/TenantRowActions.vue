<script setup lang="ts">
import { computed } from "vue"
import { Eye, Pencil, ShieldCheck, ShieldOff, Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { Tenant } from "@/tenant/types"

const props = defineProps<{ row: Tenant; canEdit: boolean }>()

const emit = defineEmits<{
  detail: [row: Tenant]
  edit: [row: Tenant]
  activate: [row: Tenant]
  deactivate: [row: Tenant]
  delete: [row: Tenant]
}>()

const actions = computed<RowAction[]>(() => {
  const list: RowAction[] = [
    { key: "detail", label: "详情", icon: Eye, onClick: () => emit("detail", props.row) },
  ]
  if (props.canEdit) {
    list.push({ key: "edit", label: "编辑", icon: Pencil, onClick: () => emit("edit", props.row) })
  }
  if (props.canEdit && props.row.status === "inactive") {
    list.push({ key: "activate", label: "激活", icon: ShieldCheck, onClick: () => emit("activate", props.row) })
  }
  if (props.canEdit && props.row.status === "active") {
    list.push({ key: "deactivate", label: "停用", icon: ShieldOff, onClick: () => emit("deactivate", props.row) })
  }
  if (props.canEdit) {
    list.push({ key: "delete", label: "删除", icon: Trash2, variant: "destructive", onClick: () => emit("delete", props.row) })
  }
  return list
})
</script>

<template>
  <RowActions :actions="actions" />
</template>
