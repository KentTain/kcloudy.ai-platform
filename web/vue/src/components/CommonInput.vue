<script setup lang="ts">
/**
 * CommonInput 输入框组件
 * 基于 shadcn-vue Input 样式，扩展 clearable/error/prefix/suffix
 */
import { ref } from "vue";
import { XIcon } from "@lucide/vue";
import { cn } from "@/lib/utils";

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

withDefaults(defineProps<Props>(), {
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

const handleInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value;
  emit("update:modelValue", value);
  emit("input", event);
};

const handleClear = () => {
  emit("update:modelValue", "");
  emit("clear");
  inputRef.value?.focus();
};

const focus = () => inputRef.value?.focus();
const blur = () => inputRef.value?.blur();

defineExpose({ focus, blur });

const sizeClasses: Record<string, string> = {
  sm: "h-7 text-xs",
  md: "h-8 text-sm",
  lg: "h-10 text-base",
};
</script>

<template>
  <div class="flex flex-col gap-1">
    <div
      :class="cn(
        'relative flex items-center rounded-md border bg-background transition-colors focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50',
        error ? 'border-destructive' : 'border-input',
        disabled && 'opacity-50 cursor-not-allowed',
        sizeClasses[size]
      )"
    >
      <div v-if="$slots.prefix" class="pl-3 text-muted-foreground">
        <slot name="prefix" />
      </div>
      <input
        ref="inputRef"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :class="cn(
          'w-full min-w-0 bg-transparent outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed',
          !$slots.prefix && 'pl-3',
          !$slots.suffix && !clearable && 'pr-3'
        )"
        @input="handleInput"
        @focus="emit('focus', $event)"
        @blur="emit('blur', $event)"
      />
      <button
        v-if="clearable && modelValue && !disabled"
        type="button"
        class="pr-2 text-muted-foreground hover:text-foreground transition-colors"
        @click="handleClear"
      >
        <XIcon class="size-4" />
      </button>
      <div v-if="$slots.suffix" class="pr-3 text-muted-foreground">
        <slot name="suffix" />
      </div>
    </div>
    <div v-if="error" class="text-destructive text-xs">
      {{ error }}
    </div>
  </div>
</template>
