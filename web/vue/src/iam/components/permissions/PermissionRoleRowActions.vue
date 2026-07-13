<script setup lang="ts">
import { computed } from "vue"
import { Settings } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { Role } from "@/iam/types"

const props = defineProps<{ row: Role }>()

const emit = defineEmits<{
  assignPermissions: [row: Role]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "assignPermissions", label: "分配权限", icon: Settings, onClick: () => emit("assignPermissions", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
