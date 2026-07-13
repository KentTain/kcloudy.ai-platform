<script setup lang="ts">
import { computed } from "vue"
import { Eye, Pencil, Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { Module } from "@/tenant/types/admin"

const props = defineProps<{ row: Module }>()

const emit = defineEmits<{
  detail: [row: Module]
  edit: [row: Module]
  delete: [row: Module]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "detail", label: "详情", icon: Eye, onClick: () => emit("detail", props.row) },
  { key: "edit", label: "编辑", icon: Pencil, onClick: () => emit("edit", props.row) },
  { key: "delete", label: "删除", icon: Trash2, variant: "destructive", onClick: () => emit("delete", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
