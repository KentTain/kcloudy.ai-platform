<script setup lang="ts">
interface Props {
  title?: string;
}

withDefaults(defineProps<Props>(), {
  title: "",
});
</script>

<template>
  <div class="rounded-lg border border-gray-200 bg-white shadow-sm">
    <div v-if="title || $slots.header" class="border-b border-gray-200 px-6 py-4">
      <slot name="header">
        <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
      </slot>
    </div>
    <div class="px-6 py-4">
      <slot />
    </div>
  </div>
</template>
