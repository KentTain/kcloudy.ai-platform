<template>
  <!-- py-0.5 -->
  <div class="relative" :style="nodeStyle">
    <div
      v-if="showLine && level > 0 && !isLastNode"
      :class="['pointer-events-none absolute top-0 bottom-0 w-px', lineBgClass]"
      :style="{ left: '0.75rem', top: '0.75rem' }"></div>
    <div class="relative min-h-8 py-px">
      <div
        v-if="showLine && level > 0"
        :class="['pointer-events-none absolute top-0 left-0 rounded-bl-[6px] border-b border-l', lineClass]"
        :style="{ height: '1rem', left: '-0.75rem', width: '0.75rem' }"></div>
      <div
        :style="rowStyle"
        :class="[
          'flex w-full items-center rounded-sm px-1.5 whitespace-nowrap',
          { 'py-px': showLine },
          { 'py-1': !showLine },
          { 'bg-gray-200': isSelected && !showLine && !dark },
          { 'bg-gray-700': isSelected && !showLine && dark },
          { 'hover:bg-gray-100': !isSelected && !showLine && !dark },
          { 'hover:bg-gray-700': !isSelected && !showLine && dark },
          { 'bg-gray-100': isSelected && showLine && !dark },
          { 'bg-gray-700': isSelected && showLine && dark },
          { 'hover:bg-gray-100': !isSelected && showLine && !node.disabled && !dark },
          { 'hover:bg-gray-700': !isSelected && showLine && !node.disabled && dark },
          { 'cursor-not-allowed': node.disabled },
          { 'cursor-pointer': !node.disabled },
        ]"
        @mousedown="onRowMouseDown"
        @click="onNodeClick">
        <button
          v-if="showExpandIcon"
          :class="['mr-2 inline-flex h-4 w-4 items-center justify-center', dark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700']"
          @mousedown.prevent
          @click.stop="onExpand">
          <!-- Loading spinner -->
          <svg v-if="loading" class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-10" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <!-- Expand/collapse arrow -->
          <div v-else>
            <slot v-if="!isExpanded" name="expand">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4 transition-transform">
                <path
                  fill-rule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clip-rule="evenodd" />
              </svg>
            </slot>

            <slot v-else name="collapse">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4 rotate-90 transition-transform">
                <path
                  fill-rule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clip-rule="evenodd" />
              </svg>
            </slot>
          </div>
        </button>

        <span v-else :class="['flex', 'w-6']"> <slot name="leaf-icon" /> </span>

        <Checkbox
          v-if="checkable"
          :checked="isSelected"
          class="inline-block size-4"
          :disabled="node.disabled"
          :indeterminate="cascade && isIndeterminate"
          @click.stop />

        <slot name="label" :node="node" :level="level" :is-selected="isSelected">
          <span
            :class="[
              'block min-w-0 flex-1 truncate text-sm whitespace-nowrap',
              { 'px-2 py-1': showLine && !node.disabled },
              { 'px-2 text-gray-500': node.disabled && showLine && !dark },
              { 'text-gray-500': node.disabled && !showLine && !dark },
              { 'px-2 text-gray-400': node.disabled && showLine && dark },
              { 'text-gray-400': node.disabled && !showLine && dark },
              { 'text-gray-200': !node.disabled && dark },
            ]">
            <span class="truncate" :title="node.label">{{ node.label }}</span>
          </span>
        </slot>
      </div>
    </div>

    <div v-if="hasChildren && isExpanded" class="relative block w-full">
      <TreeNode
        v-for="(child, index) in node.children"
        :key="child.value"
        :node="child"
        :level="level + 1"
        :is-last-node="index === node.children.length - 1"
        :selected-values="selectedValues"
        :checkable="checkable"
        :cascade="cascade"
        :show-line="showLine"
        :dark="dark"
        :expand-on-row-click="expandOnRowClick"
        :expanded-values="expandedValues"
        :load-data="loadData"
        @update-expanded="onChildUpdateExpanded"
        @on-expand="onChildExpand"
        @on-node-click="onChildNodeClick">
        <template #label="slotProps"> <slot name="label" v-bind="slotProps" /> </template>

        <template #expand="slotProps"> <slot name="expand" v-bind="slotProps" /> </template>

        <template #collapse="slotProps"> <slot name="collapse" v-bind="slotProps" /> </template>
        <template #leaf-icon="slotProps"> <slot name="leaf-icon" v-bind="slotProps" /> </template>
      </TreeNode>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { VNode } from "vue";
import { Comment, computed, Fragment, ref, Text, watch } from "vue";

import { Checkbox } from "@/components/ui/checkbox";
import type { TreeNodeEmits, TreeNodeProps, TreeNodeType } from "./types";

type TreeNodeLabelSlotProps = {
  isSelected: boolean;
  level: number;
  node: TreeNodeType;
};
type EmptySlotProps = Record<string, never>;

const emit = defineEmits<TreeNodeEmits>();
const slots = defineSlots<{
  collapse?: (props?: EmptySlotProps) => VNode[];
  expand?: (props?: EmptySlotProps) => VNode[];
  label?: (props: TreeNodeLabelSlotProps) => VNode[];
  "leaf-icon"?: (props?: EmptySlotProps) => VNode[];
}>();
const props = withDefaults(defineProps<TreeNodeProps>(), {
  cascade: false,
  checkable: false,
  dark: false,
  expandedValues: () => [],
  expandOnRowClick: false,
  isLastNode: false,
  loadData: undefined,
  selectedValues: () => [],
});

const hasSlotContent = (nodes?: VNode[]): boolean => {
  return (
    nodes?.some((node) => {
      if (node.type === Comment) {
        return false;
      }
      if (node.type === Text) {
        return String(node.children).trim().length > 0;
      }
      if (node.type === Fragment && Array.isArray(node.children)) {
        return hasSlotContent(node.children as VNode[]);
      }
      return true;
    }) ?? false
  );
};

const hasLeafIconContent = () => hasSlotContent(slots["leaf-icon"]?.());

const isExpanded = computed(
  () => props.node.value !== undefined && props.expandedValues.includes(props.node.value)
);
const loading = ref(false);
const nodeStyle = computed(() => {
  if (!props.showLine || props.level === 0) {
    return undefined;
  }
  return { paddingLeft: "1.5rem" };
});
const rowStyle = computed(() => {
  if (props.showLine || props.level === 0) {
    return undefined;
  }
  return { paddingLeft: `${props.level * 1.5 + 0.375}rem` };
});
const hasChildren = computed(() => props.node.children && props.node.children.length > 0);
const showExpandIcon = computed(() => hasChildren.value || props.node.isLeaf === false);
const isSelected = computed(() => props.selectedValues.includes(props.node.value));
const lineClass = computed(() => (props.dark ? "border-gray-600" : "border-gray-200"));
const lineBgClass = computed(() => (props.dark ? "bg-gray-600" : "bg-gray-200"));
const manuallyCollapsed = ref(false);

const isIndeterminate = computed(() => {
  if (!hasChildren.value || !props.cascade) {
    return false;
  }

  const childrenSelected =
    props.node.children?.some((child) => props.selectedValues.includes(child.value)) ?? false;

  const allChildrenSelected =
    props.node.children?.every((child) => props.selectedValues.includes(child.value)) ?? false;

  return childrenSelected && !allChildrenSelected && !isSelected.value;
});

// 判断当前节点是否是目标值的父节点
const isParentOfSelected = (node: TreeNodeType, selectedValue: TreeNodeType["value"]): boolean => {
  if (!node.children) {
    return false;
  }
  return node.children.some((child) => {
    if (child.value === selectedValue) {
      return true;
    }
    return isParentOfSelected(child, selectedValue);
  });
};

watch(
  () => props.selectedValues,
  (newValues) => {
    if (manuallyCollapsed.value) {
      return;
    }

    // 如果当前节点被选中，或者是选中节点的父节点，则展开
    const shouldExpand = newValues.some((value) => {
      return isParentOfSelected(props.node, value);
    });

    // 不是懒加载节点才自动展开
    if (
      (shouldExpand || props.selectedValues.includes(props.node.value)) &&
      !(props.node.isLeaf === false && !hasChildren.value && props.loadData)
    ) {
      emit("update-expanded", props.node, true);
    }
  },
  { immediate: true }
);

const onExpand = async (event: Event) => {
  event.stopPropagation();

  // 如果节点没有子节点且 isLeaf 为 false 且有 loadData 函数，需要加载数据
  if (!hasChildren.value && props.node.isLeaf === false && !isExpanded.value && props.loadData) {
    loading.value = true;
    try {
      // 使用回调加载数据
      props.loadData(props.node, (children: TreeNodeType[]) => {
        props.node.children = children;
        loading.value = false;
        emit("update-expanded", props.node, true);
      });
    } catch (error) {
      console.error("加载子节点失败:", error);
      loading.value = false;
    }
  } else {
    emit("update-expanded", props.node, !isExpanded.value);
  }
  emit("on-expand", props.node);
};

const onChildExpand = (node: TreeNodeType) => emit("on-expand", node);
const onChildUpdateExpanded = (node: TreeNodeType, expanded: boolean) =>
  emit("update-expanded", node, expanded);

const onRowMouseDown = (event: MouseEvent) => {
  if (props.expandOnRowClick && showExpandIcon.value && event.detail > 1) {
    event.preventDefault();
  }
};

const onNodeClick = async (event: Event) => {
  if (!props.node.disabled) {
    if (props.expandOnRowClick && showExpandIcon.value) {
      const wasExpanded = isExpanded.value;
      await onExpand(event);

      manuallyCollapsed.value = wasExpanded;
    }

    emit("on-node-click", props.node);
  }
};

const onChildNodeClick = (node: TreeNodeType) => emit("on-node-click", node);
</script>
