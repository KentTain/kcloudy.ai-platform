<script setup lang="ts">
import { computed } from "vue"
import { Eye } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { Organization } from "@/iam/types"

const props = defineProps<{ row: Organization }>()

const emit = defineEmits<{
  view: [row: Organization]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "view", label: "查看", icon: Eye, onClick: () => emit("view", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
