<script setup lang="ts">
import { computed } from "vue"
import { ExternalLink, RefreshCw, Wifi, Pencil, Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { Marketplace } from "@/tenant/types/marketplace"

const props = defineProps<{
  row: Marketplace
  isTesting: boolean
  testSuccess: boolean
}>()

const emit = defineEmits<{
  browse: [row: Marketplace]
  checkUpdates: [row: Marketplace]
  test: [row: Marketplace]
  edit: [row: Marketplace]
  delete: [row: Marketplace]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "browse", label: "浏览", icon: ExternalLink, disabled: !props.row.is_enabled, onClick: () => emit("browse", props.row) },
  { key: "checkUpdates", label: "检查更新", icon: RefreshCw, disabled: !props.row.is_enabled, onClick: () => emit("checkUpdates", props.row) },
  { key: "test", label: props.testSuccess ? "正常" : "测试", icon: Wifi, disabled: props.isTesting, onClick: () => emit("test", props.row) },
  { key: "edit", label: "编辑", icon: Pencil, onClick: () => emit("edit", props.row) },
  { key: "delete", label: "删除", icon: Trash2, variant: "destructive", onClick: () => emit("delete", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
