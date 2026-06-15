<template>
  <Popover v-model:open="computedOpen">
    <PopoverTrigger as-child>
      <div
        ref="triggerRef"
        :class="
          cn(
            'border-input ring-offset-background flex min-h-9 w-full cursor-pointer items-center gap-2 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs',
            'focus-within:ring-ring mx-mx focus-visible:border-ring focus-within:outline-none',
            disabled && 'cursor-not-allowed opacity-50',
            props.class,
          )
        "
        @click="handleTriggerClick"
        @mouseenter="isHovering = true"
        @mouseleave="isHovering = false">
        <!-- 左侧内容区 -->
        <div :class="cn('flex flex-1 items-center gap-2', multiple ? 'flex-wrap' : 'truncate')">
          <!-- 多选：显示选中的标签（在输入框内） -->
          <template v-if="multiple">
            <div
              v-for="node in selectedNodes"
              :key="node.id"
              class="bg-secondary text-secondary-foreground inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium">
              <span class="max-w-[150px] truncate">{{ node.name }}</span>
              <X v-if="!disabled" class="hover:text-destructive size-3 cursor-pointer transition-colors" @click.stop="handleRemove(node)" />
            </div>

            <!-- 搜索输入框 -->
            <input
              v-if="searchable"
              v-model="searchQuery"
              type="text"
              :placeholder="selectedNodes.length === 0 ? placeholder : ''"
              :disabled="disabled"
              class="placeholder:text-muted-foreground min-w-[120px] flex-1 border-none bg-transparent outline-none"
              @click.stop
              @focus="isOpen = true"
              @keydown="handleKeyDown" />
            <span v-else-if="selectedNodes.length === 0" class="text-muted-foreground flex-1">
              {{ placeholder }}
            </span>
          </template>

          <!-- 单选：显示文本或搜索输入 -->
          <template v-else>
            <input
              v-if="searchable"
              v-model="singleSearchDisplay"
              type="text"
              :placeholder="selectedNode ? '' : placeholder"
              :disabled="disabled"
              class="placeholder:text-muted-foreground flex h-full w-full border-none bg-transparent outline-none"
              @click.stop
              @focus="isOpen = true" />
            <span v-else-if="selectedNode" class="flex-1 truncate">{{ selectedNode.name }}</span>
            <span v-else class="text-muted-foreground flex-1">{{ placeholder }}</span>
          </template>
        </div>

        <!-- 右侧图标区 -->
        <div class="flex shrink-0 items-center gap-1">
          <!-- 清除按钮（单选、有值且 hover 时显示） -->
          <X
            v-if="clearable && !disabled && !multiple && selectedNode && isHovering"
            class="hover:text-destructive size-4 shrink-0 cursor-pointer opacity-50 transition-colors"
            @click.stop="handleClear" />

          <!-- 下拉图标 -->
          <ChevronDown :class="cn('size-4 shrink-0 opacity-50 transition-transform', isOpen && 'rotate-180')" />
        </div>
      </div>
    </PopoverTrigger>

    <PopoverContent
      :align="align"
      :side-offset="4"
      position="popper"
      :style="sameWidth ? { width: triggerWidth ? `${triggerWidth}px` : 'auto' } : undefined"
      :class="
        cn(
          'bg-popover text-popover-foreground z-50 max-h-[320px] overflow-hidden rounded-md border p-0 shadow-md outline-none',
          !sameWidth && 'w-auto min-w-[200px]',
        )
      "
      @open-auto-focus.prevent>
      <!-- 搜索框（非多选模式或不可编辑触发器时显示在顶部）预留功能，暂不启用 -->
      <div v-if="false" class="border-b p-2">
        <div class="relative">
          <Search class="text-muted-foreground absolute top-1/2 left-2 size-4 -translate-y-1/2" />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="searchPlaceholder"
            class="border-input placeholder:text-muted-foreground focus:border-ring w-full rounded-md border py-1.5 pr-3 pl-8 text-sm outline-none" />
        </div>
      </div>

      <!-- 树形内容 -->
      <div class="max-h-[260px] overflow-y-auto">
        <div class="p-2">
          <!-- 加载中 -->
          <div v-if="loading && filteredData.length === 0" class="flex items-center justify-center py-6">
            <span class="text-muted-foreground text-sm">{{ loadingText }}</span>
          </div>

          <!-- 树 -->
          <Tree
            v-else-if="filteredData.length > 0"
            :data="filteredData"
            :model-value="selectedValues"
            :multiple="multiple"
            :checkable="checkable"
            :cascade="cascade"
            :show-line="showLine"
            :default-expand-level="defaultExpandLevel"
            @update:model-value="handleTreeUpdate"
            @node-click="handleNodeClick">
            <template #label="{ node }">
              <div class="group/folder-label flex min-w-0 flex-1 truncate pl-0 pr-0 py-0.5 text-sm whitespace-nowrap">
                <div class="flex-1 truncate">{{ node.name }}</div>
              </div>
            </template>
          </Tree>

          <!-- 空状态 -->
          <div v-else class="flex flex-col items-center justify-center px-4 py-6">
            <p class="text-muted-foreground text-sm">{{ emptyText }}</p>
          </div>
        </div>
      </div>
    </PopoverContent>
  </Popover>
</template>

<script setup lang="ts">
/**
 * TreeSelect 树选择器组件
 * 支持单选/多选、搜索、级联选择等功能
 *
 * @example
 * ```vue
 * <TreeSelect
 *   v-model="selectedId"
 *   :data="treeData"
 *   placeholder="请选择..."
 * />
 * ```
 */
import { ChevronDown, Search, X } from "@lucide/vue";
import { computed, ref, watch } from "vue";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tree } from "@/components/common/data-display/tree";
import type { TreeSelectNode } from "@/framework/types/tree";
import { cn } from "@/lib/utils";

/** 选中值类型 */
type TreeSelectValue = string | number;
/** v-model 值类型 */
type TreeSelectModelValue = TreeSelectValue | TreeSelectValue[] | null;

export interface TreeSelectProps {
  /** 下拉框对齐方式 */
  align?: "start" | "center" | "end";
  /** 是否级联选择 */
  cascade?: boolean;
  /** 是否显示复选框 */
  checkable?: boolean;
  /** 自定义类名 */
  class?: string;
  /** 是否可清空 */
  clearable?: boolean;
  /** 树形数据（使用 TreeSelectNode 类型） */
  data: TreeSelectNode[];
  /** 默认展开层级 */
  defaultExpandLevel?: number;
  /** 是否禁用 */
  disabled?: boolean;
  /** 空状态文本 */
  emptyText?: string;
  /** 是否正在加载 */
  loading?: boolean;
  /** 加载中文本 */
  loadingText?: string;
  /** 绑定值 - 单选模式为单个值，多选模式为数组 */
  modelValue?: TreeSelectModelValue;
  /** 是否多选模式 */
  multiple?: boolean;
  /** 占位符 */
  placeholder?: string;
  /** 下拉框是否与触发器同宽 */
  sameWidth?: boolean;
  /** 是否可搜索 */
  searchable?: boolean;
  /** 搜索占位符 */
  searchPlaceholder?: string;
  /** 是否显示连接线 */
  showLine?: boolean;
}

const props = withDefaults(defineProps<TreeSelectProps>(), {
  align: "start",
  cascade: false,
  checkable: false,
  clearable: false,
  defaultExpandLevel: 1,
  disabled: false,
  emptyText: "暂无数据",
  loading: false,
  loadingText: "加载中...",
  multiple: false,
  placeholder: "请选择...",
  sameWidth: true,
  searchable: false,
  searchPlaceholder: "搜索...",
  showLine: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: TreeSelectModelValue];
  search: [query: string];
  "node-click": [node: TreeSelectNode];
}>();

// 状态
const isOpen = ref(false);
const searchQuery = ref("");
const triggerRef = ref<HTMLElement | null>(null);
const isHovering = ref(false);

// 触发器宽度
const triggerWidth = computed(() => triggerRef.value?.offsetWidth);

// 拦截禁用状态下的弹窗打开
const computedOpen = computed({
  get: () => isOpen.value,
  set: (val) => {
    if (!props.disabled) {
      isOpen.value = val;
    }
  },
});

// 禁用状态时自动关闭弹窗
watch(
  () => props.disabled,
  (disabled) => {
    if (disabled) {
      isOpen.value = false;
    }
  },
);

// 选中的值数组
const selectedValues = computed(() => {
  if (props.modelValue == null) return [];
  return props.multiple ? (Array.isArray(props.modelValue) ? props.modelValue : []) : [props.modelValue];
});

// 根据值查找节点
const findNodesByValues = (nodes: TreeSelectNode[], values: TreeSelectValue[]): TreeSelectNode[] => {
  const result: TreeSelectNode[] = [];
  for (const node of nodes) {
    if (values.includes(node.id)) {
      result.push(node);
    }
    if (node.children && node.children.length > 0) {
      result.push(...findNodesByValues(node.children, values));
    }
  }
  return result;
};

// 已选中的节点列表
const selectedNodes = computed(() => findNodesByValues(props.data, selectedValues.value));

// 单选模式下当前选中的节点
const selectedNode = computed(() => (props.multiple ? null : selectedNodes.value[0] || null));

// 单选可搜索模式下输入框显示值
const singleSearchDisplay = computed({
  get: () => {
    if (searchQuery.value) return searchQuery.value;
    return selectedNode.value?.name || "";
  },
  set: (value: string) => {
    searchQuery.value = value;
  },
});

// 递归过滤树节点
const filterTree = (nodes: TreeSelectNode[], query: string): TreeSelectNode[] => {
  if (!query.trim()) return nodes;
  const lowerQuery = query.toLowerCase();
  return nodes
    .map((node) => {
      const nameMatch = node.name.toLowerCase().includes(lowerQuery);
      const filteredChildren = node.children ? filterTree(node.children, query) : [];
      if (nameMatch || filteredChildren.length > 0) {
        return {
          ...node,
          children: nameMatch ? node.children || [] : filteredChildren,
        };
      }
      return null;
    })
    .filter((node): node is TreeSelectNode => node !== null);
};

// 过滤后的数据
const filteredData = computed(() => {
  if (!searchQuery.value.trim()) return props.data;
  return filterTree(props.data, searchQuery.value);
});

// 处理树组件的值更新
const handleTreeUpdate = (values: TreeSelectValue[]) => {
  if (props.multiple) {
    emit("update:modelValue", values.length > 0 ? values : []);
  } else {
    emit("update:modelValue", values.length > 0 ? values[values.length - 1] : null);
    if (values.length > 0) {
      isOpen.value = false;
      searchQuery.value = "";
    }
  }
};

// 处理节点点击
const handleNodeClick = ({ node }: { node: TreeSelectNode; level: number }) => {
  emit("node-click", node);
  if (!props.multiple && !props.checkable) {
    emit("update:modelValue", node.id);
    isOpen.value = false;
    searchQuery.value = "";
  }
};

// 处理触发器点击（确保点击输入框区域也能打开下拉）
const handleTriggerClick = (event: MouseEvent) => {
  if (props.disabled) {
    event.preventDefault();
    event.stopPropagation();
    return;
  }
  isOpen.value = true;
};

// 移除选中项（多选模式）
const handleRemove = (node: TreeSelectNode) => {
  if (!props.multiple || props.disabled) return;
  const newValues = selectedValues.value.filter((v) => v !== node.id);
  emit("update:modelValue", newValues);
};

// 清空选择
const handleClear = () => {
  if (props.disabled) return;
  emit("update:modelValue", props.multiple ? [] : null);
  searchQuery.value = "";
};

// 处理按键事件 - 多选模式下按删除键删除最后一个标签
const handleKeyDown = (event: KeyboardEvent) => {
  if (props.multiple && event.key === "Backspace" && searchQuery.value === "" && selectedNodes.value.length > 0) {
    event.preventDefault();
    const lastNode = selectedNodes.value[selectedNodes.value.length - 1];
    if (lastNode) {
      handleRemove(lastNode);
    }
  }
};

// 监听搜索关键词变化
watch(searchQuery, (newQuery) => {
  emit("search", newQuery);
});

// 下拉框关闭时清空搜索
watch(isOpen, (open) => {
  if (!open) {
    searchQuery.value = "";
  }
});
</script>
