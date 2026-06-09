<template>
  <TooltipProvider>
    <Tooltip>
      <TooltipTrigger as-child>
        <div ref="triggerRef" :class="props.class" @mouseenter="handleTriggerMouseEnter"><slot /></div>
      </TooltipTrigger>
      <slot name="tooltip-content">
        <!-- 当仅在省略时显示时, 使用 isOverflow 来判断内容是否溢出 -->
        <TooltipContent class="max-w-xs text-wrap z-101" :class="props.contentClass" v-if="onlyEllipsisOpen ? isOverflow : true">
          <span class="block w-full whitespace-normal wrap-break-word" v-html="content"></span>
        </TooltipContent>
      </slot>
    </Tooltip>
  </TooltipProvider>
</template>
<script lang="ts" setup>
import { measureLineStats, measureNaturalWidth, prepareWithSegments } from "@chenglou/pretext";
import type { TooltipTriggerProps } from "reka-ui";
import { type HTMLAttributes, ref, useTemplateRef } from "vue";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface Props extends TooltipTriggerProps {
  class?: HTMLAttributes["class"];
  content: string;
  contentClass?: HTMLAttributes["class"];
  onlyEllipsisOpen?: boolean;
}

const props = defineProps<Props>();

const triggerRef = useTemplateRef<HTMLDivElement>("triggerRef");
const isOverflow = ref(false);

function isGreaterThan(a: number, b: number, epsilon = 0.5) {
  return a - b > epsilon;
}

function getCssNumber(value: string) {
  return Number.parseFloat(value) || 0;
}

function getPadding(style: CSSStyleDeclaration) {
  const paddingLeft = getCssNumber(style.paddingLeft);
  const paddingRight = getCssNumber(style.paddingRight);
  const paddingTop = getCssNumber(style.paddingTop);
  const paddingBottom = getCssNumber(style.paddingBottom);

  return {
    bottom: paddingBottom,
    left: paddingLeft,
    right: paddingRight,
    top: paddingTop,
  };
}

// pretext 需要与页面渲染一致的 font shorthand，才能得到尽量贴近 DOM 的测量结果。
function getFont(style: CSSStyleDeclaration) {
  return [style.fontStyle, style.fontVariant, style.fontWeight, style.fontSize, style.fontFamily].filter(Boolean).join(" ");
}

function getLineHeight(style: CSSStyleDeclaration) {
  const lineHeight = getCssNumber(style.lineHeight);
  if (lineHeight > 0) {
    return lineHeight;
  }

  return getCssNumber(style.fontSize) * 1.2;
}

function isNoWrap(style: CSSStyleDeclaration) {
  return style.whiteSpace === "nowrap" || style.whiteSpace === "pre";
}

// 将常见 white-space / word-break 样式映射到 pretext 支持的配置。
function getPrepareOptions(style: CSSStyleDeclaration) {
  return {
    whiteSpace:
      style.whiteSpace === "pre" || style.whiteSpace === "pre-wrap" || style.whiteSpace === "break-spaces" || style.whiteSpace === "pre-line"
        ? "pre-wrap"
        : "normal",
    wordBreak: style.wordBreak === "keep-all" ? "keep-all" : "normal",
  } as const;
}

/** 计算文本是否溢出，SmartTooltip 仅在内容溢出时显示 */
function handleTriggerMouseEnter() {
  if (!triggerRef.value) {
    return;
  }

  const el = triggerRef.value;
  const text = el.textContent ?? "";

  if (text.trim().length === 0) {
    isOverflow.value = false;
    return;
  }

  const style = window.getComputedStyle(el, null);
  const { top, left, right, bottom } = getPadding(style);

  // 这里使用 content box 尺寸，避免把 padding 误算进可用文本区域。
  const contentWidth = el.clientWidth - left - right;
  const contentHeight = el.clientHeight - top - bottom;

  if (contentWidth <= 0) {
    isOverflow.value = false;
    return;
  }

  const prepared = prepareWithSegments(text, getFont(style), getPrepareOptions(style));
  const naturalWidth = measureNaturalWidth(prepared);
  const { lineCount } = measureLineStats(prepared, contentWidth);
  const textHeight = lineCount * getLineHeight(style);

  // 单行省略看横向是否放得下；多行场景主要看按当前宽度换行后的总高度是否超出容器。
  isOverflow.value = (isNoWrap(style) && isGreaterThan(naturalWidth, contentWidth)) || (contentHeight > 0 && isGreaterThan(textHeight, contentHeight));
}
</script>
