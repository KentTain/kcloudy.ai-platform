<script setup lang="ts">
import { computed } from "vue"
import { Eye, CheckCircle, Download, Play, Square, Pencil, Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { PluginDefinition } from "@/tenant/api/plugin"

const props = defineProps<{ row: PluginDefinition }>()

const emit = defineEmits<{
  detail: [row: PluginDefinition]
  toggleEnabled: [row: PluginDefinition]
  install: [row: PluginDefinition]
  start: [row: PluginDefinition]
  stop: [row: PluginDefinition]
  edit: [row: PluginDefinition]
  delete: [row: PluginDefinition]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "detail", label: "详情", icon: Eye, onClick: () => emit("detail", props.row) },
  { key: "toggleEnabled", label: props.row.is_enabled ? "禁用" : "启用", icon: CheckCircle, onClick: () => emit("toggleEnabled", props.row) },
  { key: "install", label: "安装", icon: Download, onClick: () => emit("install", props.row) },
  { key: "start", label: "启动", icon: Play, onClick: () => emit("start", props.row) },
  { key: "stop", label: "停止", icon: Square, onClick: () => emit("stop", props.row) },
  { key: "edit", label: "编辑", icon: Pencil, onClick: () => emit("edit", props.row) },
  { key: "delete", label: "删除", icon: Trash2, variant: "destructive", onClick: () => emit("delete", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
