<!-- web/src/components/ui/AppModal.vue -->
<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

interface Props {
  open: boolean;
  title?: string;
}

withDefaults(defineProps<Props>(), {
  title: "",
});

const emit = defineEmits<{
  close: [];
}>();

// biome-ignore lint/correctness/noUnusedVariables: used in template
const onOverlayClick = () => {
  emit("close");
};

// biome-ignore lint/correctness/noUnusedVariables: used in template
const onDialogClick = (event: MouseEvent) => {
  event.stopPropagation();
};

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    emit("close");
  }
}

onMounted(() => {
  document.addEventListener("keydown", onKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click="onOverlayClick"
    >
      <div
        class="w-full max-w-[480px] rounded-lg bg-white shadow-xl"
        @click="onDialogClick"
      >
        <div v-if="title || $slots.header" class="border-b border-gray-200 px-6 py-4">
          <slot name="header">
            <h2 class="text-lg font-semibold text-gray-800">{{ title }}</h2>
          </slot>
        </div>
        <div class="px-6 py-4">
          <slot />
        </div>
        <div v-if="$slots.footer" class="border-t border-gray-200 px-6 py-4">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>