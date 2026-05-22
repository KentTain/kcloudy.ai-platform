<script setup lang="ts">
/**
 * CommonInput 输入框组件
 */
import { computed, ref } from "vue";

interface Props {
  modelValue?: string;
  type?: "text" | "password" | "email" | "number";
  placeholder?: string;
  disabled?: boolean;
  readonly?: boolean;
  error?: string;
  size?: "sm" | "md" | "lg";
  clearable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "",
  type: "text",
  size: "md",
  clearable: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  input: [event: Event];
  focus: [event: FocusEvent];
  blur: [event: FocusEvent];
  clear: [];
}>();

const inputRef = ref<HTMLInputElement>();
const isFocused = ref(false);

const inputClasses = computed(() => [
  "common-input",
  `common-input--${props.size}`,
  {
    "common-input--focused": isFocused.value,
    "common-input--disabled": props.disabled,
    "common-input--error": props.error,
  },
]);

const handleInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value;
  emit("update:modelValue", value);
  emit("input", event);
};

const handleFocus = (event: FocusEvent) => {
  isFocused.value = true;
  emit("focus", event);
};

const handleBlur = (event: FocusEvent) => {
  isFocused.value = false;
  emit("blur", event);
};

const handleClear = () => {
  emit("update:modelValue", "");
  emit("clear");
  inputRef.value?.focus();
};

const focus = () => inputRef.value?.focus();
const blur = () => inputRef.value?.blur();

defineExpose({ focus, blur });
</script>

<template>
  <div class="common-input-wrapper">
    <div :class="inputClasses">
      <div v-if="$slots.prefix" class="common-input__prefix">
        <slot name="prefix" />
      </div>
      <input
        ref="inputRef"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        class="common-input__inner"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <div v-if="clearable && modelValue && !disabled" class="common-input__clear" @click="handleClear">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
        </svg>
      </div>
      <div v-if="$slots.suffix" class="common-input__suffix">
        <slot name="suffix" />
      </div>
    </div>
    <div v-if="error" class="common-input__error">{{ error }}</div>
  </div>
</template>

<style scoped>
.common-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.common-input {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-ui);
  transition: all var(--transition-fast);
}

.common-input:hover:not(.common-input--disabled) {
  border-color: var(--color-primary);
}

.common-input--focused {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-border-primary);
}

.common-input--disabled {
  background-color: var(--color-surface);
  cursor: not-allowed;
}

.common-input--disabled .common-input__inner {
  cursor: not-allowed;
  color: var(--color-text-disabled);
}

.common-input--error {
  border-color: var(--color-danger);
}

.common-input--error.common-input--focused {
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
}

/* 尺寸 */
.common-input--sm .common-input__inner {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.common-input--md .common-input__inner {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
}

.common-input--lg .common-input__inner {
  padding: 0.75rem 1rem;
  font-size: 1rem;
}

.common-input__inner {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text);
  font-family: inherit;
}

.common-input__inner::placeholder {
  color: var(--color-text-disabled);
}

.common-input__prefix,
.common-input__suffix {
  display: flex;
  align-items: center;
  color: var(--color-text-muted);
  padding: 0 0.5rem;
}

.common-input__clear {
  display: flex;
  align-items: center;
  padding: 0 0.5rem;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.common-input__clear:hover {
  color: var(--color-text);
}

.common-input__error {
  color: var(--color-danger);
  font-size: 0.75rem;
}
</style>
