<script setup lang="ts">
/**
 * AppLoading 加载组件
 */
interface Props {
  size?: "sm" | "md" | "lg";
  text?: string;
  fullscreen?: boolean;
}

withDefaults(defineProps<Props>(), {
  size: "md",
  fullscreen: false,
});
</script>

<template>
  <div :class="['app-loading', `app-loading--${size}`, { 'app-loading--fullscreen': fullscreen }]">
    <div class="app-loading__spinner">
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25" />
        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
    <span v-if="text" class="app-loading__text">{{ text }}</span>
  </div>
</template>

<style scoped>
.app-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.app-loading--fullscreen {
  position: fixed;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.app-loading__spinner svg {
  animation: spin 1s linear infinite;
  color: var(--color-primary);
}

.app-loading--sm .app-loading__spinner svg {
  width: 1rem;
  height: 1rem;
}

.app-loading--md .app-loading__spinner svg {
  width: 2rem;
  height: 2rem;
}

.app-loading--lg .app-loading__spinner svg {
  width: 3rem;
  height: 3rem;
}

.app-loading__text {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
