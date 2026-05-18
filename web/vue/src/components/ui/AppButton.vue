<script setup lang="ts">
interface Props {
  variant?: "primary" | "secondary";
  disabled?: boolean;
}

withDefaults(defineProps<Props>(), {
  variant: "primary",
  disabled: false,
});

// biome-ignore lint/correctness/noUnusedVariables: used in template
const variantClasses = {
  primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300",
  secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:bg-gray-100",
};
</script>

<template>
  <button
    :class="[
      'rounded-lg px-4 py-2 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
      variantClasses[variant],
    ]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>