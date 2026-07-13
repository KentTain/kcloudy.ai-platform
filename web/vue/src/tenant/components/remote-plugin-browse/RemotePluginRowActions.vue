<script setup lang="ts">
import { computed } from "vue"
import { Download } from "@lucide/vue"
import { RowActions, type RowAction } from "@/components"
import type { RemotePlugin } from "@/tenant/types/marketplace"

const props = defineProps<{ row: RemotePlugin }>()

const emit = defineEmits<{
  sync: [row: RemotePlugin]
}>()

const actions = computed<RowAction[]>(() => [
  { key: "sync", label: "同步", icon: Download, onClick: () => emit("sync", props.row) },
])
</script>

<template>
  <RowActions :actions="actions" />
</template>
