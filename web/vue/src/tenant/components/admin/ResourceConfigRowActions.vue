<script setup lang="ts">
import { computed } from "vue"
import { Plug, Pencil, Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { ResourceConfig } from "@/tenant/types/resource"

type ResourceType = "database" | "storage" | "cache" | "queue" | "pubsub"

const props = defineProps<{
  row: ResourceConfig
  resourceType: ResourceType
  isTesting: boolean
}>()

const emit = defineEmits<{
  test: [row: ResourceConfig, type: ResourceType]
  edit: [row: ResourceConfig]
  delete: [row: ResourceConfig]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "test", label: "测试", icon: Plug, disabled: props.isTesting, onClick: () => emit("test", props.row, props.resourceType) },
  { key: "edit", label: "编辑", icon: Pencil, onClick: () => emit("edit", props.row) },
  { key: "delete", label: "删除", icon: Trash2, variant: "destructive", onClick: () => emit("delete", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
