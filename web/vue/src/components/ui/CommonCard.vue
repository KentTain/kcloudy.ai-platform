<script setup lang="ts">
/**
 * CommonCard 卡片组件
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
  <div :class="['common-card', `common-card--shadow-${shadow}`, `common-card--padding-${padding}`]">
    <div v-if="title || $slots.header" class="common-card__header">
      <slot name="header">
        <h3 class="common-card__title">{{ title }}</h3>
      </slot>
    </div>
    <div class="common-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="common-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.common-card {
  background-color: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-ui);
}

/* 阴影 */
.common-card--shadow-sm {
  box-shadow: var(--shadow-sm);
}

.common-card--shadow-md {
  box-shadow: var(--shadow-md);
}

.common-card--shadow-lg {
  box-shadow: var(--shadow-lg);
}

.common-card--shadow-none {
  box-shadow: none;
}

/* 内边距 */
.common-card--padding-sm .common-card__body {
  padding: 0.75rem;
}

.common-card--padding-md .common-card__body {
  padding: 1rem;
}

.common-card--padding-lg .common-card__body {
  padding: 1.5rem;
}

.common-card__header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.common-card__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.common-card__footer {
  padding: 1rem;
  border-top: 1px solid var(--color-border);
}
</style>
