<script setup lang="ts">
/**
 * AppButton 按钮组件
 * 支持多种变体：primary、secondary、outline、ghost、danger
 */
import { computed } from "vue";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface Props {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  block?: boolean;
  type?: "button" | "submit" | "reset";
}

const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
  size: "md",
  disabled: false,
  loading: false,
  block: false,
  type: "button",
});

const emit = defineEmits<{
  click: [event: MouseEvent];
}>();

const buttonClasses = computed(() => {
  const classes = [
    "app-button",
    `app-button--${props.variant}`,
    `app-button--${props.size}`,
  ];

  if (props.disabled || props.loading) {
    classes.push("app-button--disabled");
  }

  if (props.block) {
    classes.push("app-button--block");
  }

  if (props.loading) {
    classes.push("app-button--loading");
  }

  return classes;
});

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit("click", event);
  }
};
</script>

<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    :type="type"
    @click="handleClick"
  >
    <span v-if="loading" class="app-button__loading">
      <svg class="animate-spin" viewBox="0 0 24 24">
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
          fill="none"
          opacity="0.25"
        />
        <path
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </span>
    <span class="app-button__content">
      <slot />
    </span>
  </button>
</template>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
  border-radius: var(--radius-ui);
  transition: all var(--transition-fast);
  cursor: pointer;
  border: 1px solid transparent;
  outline: none;
}

.app-button:focus-visible {
  box-shadow: 0 0 0 2px var(--color-primary-subtle);
}

/* 尺寸 */
.app-button--sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.app-button--md {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.app-button--lg {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

/* 变体 - 主色 */
.app-button--primary {
  background-color: var(--color-primary);
  color: white;
}

.app-button--primary:hover:not(.app-button--disabled) {
  background-color: var(--color-primary-hover);
}

.app-button--primary:active:not(.app-button--disabled) {
  background-color: var(--color-primary-active);
}

/* 变体 - 辅色 */
.app-button--secondary {
  background-color: var(--color-secondary);
  color: white;
}

.app-button--secondary:hover:not(.app-button--disabled) {
  background-color: var(--color-secondary-hover);
}

/* 变体 - 描边 */
.app-button--outline {
  background-color: transparent;
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.app-button--outline:hover:not(.app-button--disabled) {
  background-color: var(--color-primary-subtle);
}

/* 变体 - 幽灵 */
.app-button--ghost {
  background-color: transparent;
  color: var(--color-text-muted);
}

.app-button--ghost:hover:not(.app-button--disabled) {
  color: var(--color-primary);
  background-color: var(--color-primary-subtle);
}

/* 变体 - 危险 */
.app-button--danger {
  background-color: var(--color-danger);
  color: white;
}

.app-button--danger:hover:not(.app-button--disabled) {
  background-color: #dc2626;
}

/* 禁用状态 */
.app-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 块级 */
.app-button--block {
  display: flex;
  width: 100%;
}

/* 加载状态 */
.app-button--loading .app-button__content {
  opacity: 0;
}

.app-button__loading {
  position: absolute;
}

.app-button__loading svg {
  width: 1em;
  height: 1em;
}
</style>
