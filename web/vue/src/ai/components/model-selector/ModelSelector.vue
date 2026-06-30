<script setup lang="ts">
import { Dialog } from "@/components";
</script>

<template>
  <Dialog v-bind="$attrs">
    <slot />
  </Dialog>
</template>
