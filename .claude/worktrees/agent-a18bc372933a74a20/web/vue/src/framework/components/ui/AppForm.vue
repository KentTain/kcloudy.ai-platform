<script setup lang="ts">
/**
 * AppForm 表单组件
 */
import { provide, reactive, ref, computed } from "vue";

interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}

interface Props {
  modelValue?: Record<string, any>;
  labelWidth?: string;
  labelPosition?: "left" | "right" | "top";
  rules?: Record<string, any[]>;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  labelWidth: "100px",
  labelPosition: "right",
  rules: () => ({}),
});

const emit = defineEmits<{
  "update:modelValue": [value: Record<string, any>];
  submit: [value: Record<string, any>];
}>();

const formState = reactive<FormState>({
  values: { ...props.modelValue },
  errors: {},
  touched: {},
});

const isValid = computed(() => Object.keys(formState.errors).length === 0);

// 提供给子组件
provide("formState", formState);
provide("labelWidth", props.labelWidth);
provide("labelPosition", props.labelPosition);

const validateField = (field: string, value: any) => {
  const rules = props.rules[field];
  if (!rules) return;

  for (const rule of rules) {
    if (rule.required && !value) {
      formState.errors[field] = rule.message || "此字段必填";
      return false;
    }
    if (rule.pattern && !rule.pattern.test(value)) {
      formState.errors[field] = rule.message || "格式不正确";
      return false;
    }
    if (rule.validator) {
      const result = rule.validator(value);
      if (result !== true) {
        formState.errors[field] = result || "验证失败";
        return false;
      }
    }
  }

  delete formState.errors[field];
  return true;
};

const setFieldValue = (field: string, value: any) => {
  formState.values[field] = value;
  formState.touched[field] = true;
  emit("update:modelValue", { ...formState.values });

  if (formState.touched[field]) {
    validateField(field, value);
  }
};

const setFieldError = (field: string, error: string) => {
  formState.errors[field] = error;
};

const validate = () => {
  let valid = true;

  Object.keys(props.rules).forEach((field) => {
    if (!validateField(field, formState.values[field])) {
      valid = false;
    }
  });

  return valid;
};

const resetForm = () => {
  formState.values = { ...props.modelValue };
  formState.errors = {};
  formState.touched = {};
};

const handleSubmit = (event: Event) => {
  event.preventDefault();

  if (validate()) {
    emit("submit", { ...formState.values });
  }
};

// 提供给子组件的方法
provide("setFieldValue", setFieldValue);
provide("setFieldError", setFieldError);

defineExpose({
  validate,
  resetForm,
  isValid,
});
</script>

<template>
  <form class="app-form" @submit="handleSubmit">
    <slot />
  </form>
</template>

<style scoped>
.app-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
