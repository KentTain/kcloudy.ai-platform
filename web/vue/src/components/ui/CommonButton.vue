<script setup lang="ts">
/**
 * CommonButton 按钮组件
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
    "common-button",
    `common-button--${props.variant}`,
    `common-button--${props.size}`,
  ];

  if (props.disabled || props.loading) {
    classes.push("common-button--disabled");
  }

  if (props.block) {
    classes.push("common-button--block");
  }

  if (props.loading) {
    classes.push("common-button--loading");
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
    <span v-if="loading" class="common-button__loading">
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
    <span class="common-button__content">
      <slot />
    </span>
  </button>
</template>

<style scoped>
.common-button {
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

.common-button:focus-visible {
  box-shadow: 0 0 0 2px var(--color-primary-subtle);
}

/* 尺寸 */
.common-button--sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.common-button--md {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.common-button--lg {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

/* 变体 - 主色 */
.common-button--primary {
  background-color: var(--color-primary);
  color: white;
}

.common-button--primary:hover:not(.common-button--disabled) {
  background-color: var(--color-primary-hover);
}

.common-button--primary:active:not(.common-button--disabled) {
  background-color: var(--color-primary-active);
}

/* 变体 - 辅色 */
.common-button--secondary {
  background-color: var(--color-secondary);
  color: white;
}

.common-button--secondary:hover:not(.common-button--disabled) {
  background-color: var(--color-secondary-hover);
}

/* 变体 - 描边 */
.common-button--outline {
  background-color: transparent;
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.common-button--outline:hover:not(.common-button--disabled) {
  background-color: var(--color-primary-subtle);
}

/* 变体 - 幽灵 */
.common-button--ghost {
  background-color: transparent;
  color: var(--color-text-muted);
}

.common-button--ghost:hover:not(.common-button--disabled) {
  color: var(--color-primary);
  background-color: var(--color-primary-subtle);
}

/* 变体 - 危险 */
.common-button--danger {
  background-color: var(--color-danger);
  color: white;
}

.common-button--danger:hover:not(.common-button--disabled) {
  background-color: #dc2626;
}

/* 禁用状态 */
.common-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 块级 */
.common-button--block {
  display: flex;
  width: 100%;
}

/* 加载状态 */
.common-button--loading .common-button__content {
  opacity: 0;
}

.common-button__loading {
  position: absolute;
}

.common-button__loading svg {
  width: 1em;
  height: 1em;
}
</style>
