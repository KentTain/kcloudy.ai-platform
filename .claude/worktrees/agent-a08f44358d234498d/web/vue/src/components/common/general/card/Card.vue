<script setup lang="ts">
/**
 * Card 卡片组件
 * 基于 shadcn-vue Card 原语，封装 shadow/padding 属性
 */
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Props {
  title?: string;
  shadow?: "sm" | "md" | "lg" | "none";
  padding?: "sm" | "md" | "lg";
}

withDefaults(defineProps<Props>(), {
  shadow: "sm",
  padding: "md",
});

// 阴影映射
const shadowClasses: Record<string, string> = {
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
  none: "",
};

// 内边距映射
const paddingClasses: Record<string, string> = {
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
};
</script>

<template>
  <Card :class="cn(shadowClasses[shadow])">
    <CardHeader v-if="title || $slots.header" class="border-b border-border">
      <slot name="header">
        <CardTitle>{{ title }}</CardTitle>
      </slot>
    </CardHeader>
    <CardContent :class="paddingClasses[padding]">
      <slot />
    </CardContent>
    <CardFooter v-if="$slots.footer" class="border-t border-border">
      <slot name="footer" />
    </CardFooter>
  </Card>
</template>
