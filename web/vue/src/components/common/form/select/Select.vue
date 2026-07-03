<script setup lang="ts">
/**
 * Select 下拉选择组件
 * 基于 shadcn-vue Select 原语，封装 options/clearable
 */
import type { AcceptableValue } from "reka-ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { XIcon } from "@lucide/vue";

import { cn } from "@/lib/utils";

interface Option {
  label: string;
  value: string | number;
  disabled?: boolean;
}

interface Props {
  modelValue?: string | number | null;
  options: Option[];
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  size?: "sm" | "md" | "lg";
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: "请选择",
  size: "md",
  clearable: false,
  disabled: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string | number | null];
  change: [value: string | number | null];
}>();

const toOriginalValue = (value: AcceptableValue) => {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const option = props.options.find((item) => String(item.value) === String(value));
  return option?.value ?? String(value);
};

const handleChange = (value: AcceptableValue) => {
  const val = toOriginalValue(value);
  emit("update:modelValue", val);
  emit("change", val);
};

const handleClear = (event: MouseEvent) => {
  event.stopPropagation();
  emit("update:modelValue", null);
  emit("change", null);
};

const sizeClasses: Record<string, string> = {
  sm: "h-7 text-xs",
  md: "h-8 text-sm",
  lg: "h-10 text-base",
};
</script>

<template>
  <div class="relative">
    <Select
      :model-value="modelValue?.toString() ?? undefined"
      :disabled="disabled"
      @update:model-value="handleChange"
    >
      <SelectTrigger :class="cn(sizeClasses[size])">
        <SelectValue :placeholder="placeholder" />
        <button
          v-if="clearable && modelValue !== null"
          type="button"
          class="absolute right-8 text-muted-foreground hover:text-foreground transition-colors"
          @click="handleClear"
        >
          <XIcon class="size-4" />
        </button>
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="option in options"
          :key="option.value"
          :value="option.value.toString()"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>
