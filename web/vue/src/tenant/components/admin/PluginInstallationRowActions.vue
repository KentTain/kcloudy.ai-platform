<script setup lang="ts">
import { computed } from "vue"
import { Trash2 } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { PluginInstallation } from "@/tenant/api/plugin"

const props = defineProps<{
  row: PluginInstallation
  isUninstalling: boolean
}>()

const emit = defineEmits<{
  uninstall: [row: PluginInstallation]
}>()

const actions = computed<RowAction[]>(() => [
  {
    key: "uninstall",
    label: props.isUninstalling ? "卸载中" : "卸载",
    icon: Trash2,
    variant: "destructive",
    disabled: props.row.status === "ACTIVE" || props.isUninstalling,
    onClick: () => emit("uninstall", props.row),
  },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
