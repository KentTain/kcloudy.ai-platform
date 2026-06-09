<script setup lang="ts">
/**
 * Button 按钮组件
 * 基于 shadcn-vue Button 原语，扩展 loading/block 属性和业务变体样式
 */
import type { ButtonVariants } from "@/components/ui/button";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { LoaderIcon } from "@lucide/vue";

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

// 业务变体 → shadcn 变体映射
const variantMap: Record<ButtonVariant, ButtonVariants["variant"]> = {
  primary: "default",
  secondary: "secondary",
  outline: "outline",
  ghost: "ghost",
  danger: "destructive",
};

const sizeMap: Record<ButtonSize, ButtonVariants["size"]> = {
  sm: "sm",
  md: "default",
  lg: "lg",
};

// 业务兼容样式覆盖：确保各变体与原 Common 组件视觉契约一致
const variantOverride: Record<ButtonVariant, string> = {
  primary: "",
  secondary: "",
  outline: "border-primary text-primary hover:bg-primary/10",
  ghost: "text-text-muted hover:text-primary hover:bg-primary/10",
  danger: "bg-destructive text-white hover:bg-destructive/90",
};

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit("click", event);
  }
};
</script>

<template>
  <Button
    :variant="variantMap[variant]"
    :size="sizeMap[size]"
    :disabled="disabled || loading"
    :type="type"
    :class="cn(block && 'w-full', variantOverride[variant])"
    @click="handleClick"
  >
    <LoaderIcon v-if="loading" class="size-4 animate-spin" />
    <slot v-else />
  </Button>
</template>
