<script setup lang="ts">
import { computed } from "vue"
import { UserX, UserCheck, X } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { OrganizationUser } from "@/iam/types"

const props = defineProps<{ row: OrganizationUser }>()

const emit = defineEmits<{
  disable: [row: OrganizationUser]
  enable: [row: OrganizationUser]
  remove: [row: OrganizationUser]
}>()

const actions = computed<RowAction[]>(() => {
  const list: RowAction[] = []
  if (props.row.status === "active") {
    list.push({ key: "disable", label: "停用", icon: UserX, onClick: () => emit("disable", props.row) })
  } else {
    list.push({ key: "enable", label: "启用", icon: UserCheck, onClick: () => emit("enable", props.row) })
  }
  list.push({ key: "remove", label: "移除", icon: X, variant: "destructive", onClick: () => emit("remove", props.row) })
  return list
})
</script>

<template>
  <RowActions :actions="actions" />
</template>
