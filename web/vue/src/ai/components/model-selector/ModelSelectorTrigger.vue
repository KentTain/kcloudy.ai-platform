<script setup lang="ts">
import { DialogTrigger } from "@/components";
</script>

<template>
  <DialogTrigger v-bind="$attrs">
    <slot />
  </DialogTrigger>
</template>
