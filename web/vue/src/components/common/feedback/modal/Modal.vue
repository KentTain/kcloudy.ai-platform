<script setup lang="ts">
/**
 * Modal 对话框组件
 * 基于 shadcn-vue Dialog 原语，封装 size/maskClosable
 */
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface Props {
  modelValue: boolean;
  title?: string;
  size?: "sm" | "md" | "lg" | "xl";
  closable?: boolean;
  maskClosable?: boolean;
}

withDefaults(defineProps<Props>(), {
  size: "md",
  closable: true,
  maskClosable: true,
});

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  close: [];
}>();

const handleOpenChange = (value: boolean) => {
  emit("update:modelValue", value);
  if (!value) {
    emit("close");
  }
};

const sizeClasses: Record<string, string> = {
  sm: "sm:max-w-[400px]",
  md: "sm:max-w-[520px]",
  lg: "sm:max-w-[680px]",
  xl: "sm:max-w-[900px]",
};
</script>

<template>
  <Dialog :open="modelValue" @update:open="handleOpenChange">
    <DialogContent
      :class="cn(sizeClasses[size], 'max-h-[90vh] flex flex-col')"
      :show-close-button="closable"
      @interact-outside="!maskClosable && $event.preventDefault()"
    >
      <DialogHeader v-if="title || $slots.header">
        <slot name="header">
          <DialogTitle>{{ title }}</DialogTitle>
        </slot>
      </DialogHeader>
      <div class="flex-1 overflow-y-auto py-4">
        <slot />
      </div>
      <DialogFooter v-if="$slots.footer">
        <slot name="footer" />
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
