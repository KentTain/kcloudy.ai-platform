<script setup lang="ts">
/**
 * AppCard 卡片组件
 */
interface Props {
  title?: string;
  shadow?: "sm" | "md" | "lg" | "none";
  padding?: "sm" | "md" | "lg";
}

withDefaults(defineProps<Props>(), {
  shadow: "sm",
  padding: "md",
});
</script>

<template>
  <div :class="['app-card', `app-card--shadow-${shadow}`, `app-card--padding-${padding}`]">
    <div v-if="title || $slots.header" class="app-card__header">
      <slot name="header">
        <h3 class="app-card__title">{{ title }}</h3>
      </slot>
    </div>
    <div class="app-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="app-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.app-card {
  background-color: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-ui);
}

/* 阴影 */
.app-card--shadow-sm {
  box-shadow: var(--shadow-sm);
}

.app-card--shadow-md {
  box-shadow: var(--shadow-md);
}

.app-card--shadow-lg {
  box-shadow: var(--shadow-lg);
}

.app-card--shadow-none {
  box-shadow: none;
}

/* 内边距 */
.app-card--padding-sm .app-card__body {
  padding: 0.75rem;
}

.app-card--padding-md .app-card__body {
  padding: 1rem;
}

.app-card--padding-lg .app-card__body {
  padding: 1.5rem;
}

.app-card__header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.app-card__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.app-card__footer {
  padding: 1rem;
  border-top: 1px solid var(--color-border);
}
</style>
