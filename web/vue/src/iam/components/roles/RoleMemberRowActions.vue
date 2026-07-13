<script setup lang="ts">
import { computed } from "vue"
import { X } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { RoleMember } from "@/iam/types"

const props = defineProps<{ row: RoleMember }>()

const emit = defineEmits<{
  remove: [row: RoleMember]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "remove", label: "移除", icon: X, variant: "destructive", onClick: () => emit("remove", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
