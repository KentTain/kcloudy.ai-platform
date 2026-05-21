<script setup lang="ts">
/**
 * AppFormItem 表单项组件
 */
import { inject, computed } from "vue";

interface Props {
  label?: string;
  prop?: string;
  required?: boolean;
}

const props = defineProps<Props>();

const formState = inject<any>("formState", {});
const setFieldValue = inject<(field: string, value: any) => void>("setFieldValue", () => {});
const setFieldError = inject<(field: string, error: string) => void>("setFieldError", () => {});
const labelWidth = inject<string>("labelWidth", "100px");
const labelPosition = inject<string>("labelPosition", "right");

const error = computed(() => (props.prop ? formState?.errors?.[props.prop] : ""));
</script>

<template>
  <div :class="['app-form-item', { 'app-form-item--error': error, 'app-form-item--required': required }]">
    <label
      v-if="label"
      :class="['app-form-item__label', `app-form-item__label--${labelPosition}`]"
      :style="labelPosition !== 'top' ? { width: labelWidth } : undefined"
    >
      {{ label }}
    </label>
    <div class="app-form-item__content">
      <slot />
      <div v-if="error" class="app-form-item__error">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.app-form-item {
  display: flex;
  gap: 0.5rem;
}

.app-form-item--required .app-form-item__label::before {
  content: "*";
  color: var(--color-danger);
  margin-right: 0.25rem;
}

.app-form-item__label {
  flex-shrink: 0;
  color: var(--color-text);
  font-size: 0.875rem;
}

.app-form-item__label--right {
  text-align: right;
}

.app-form-item__label--top {
  margin-bottom: 0.25rem;
}

.app-form-item__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.app-form-item__error {
  color: var(--color-danger);
  font-size: 0.75rem;
}
</style>
