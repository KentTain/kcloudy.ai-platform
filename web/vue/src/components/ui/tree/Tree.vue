<template>
  <div class="w-full">
    <TreeNode
      v-for="(item, index) in data"
      :key="item.value"
      :node="item"
      :level="0"
      :is-last-node="index === data.length - 1"
      :selected-values="selectedValues"
      :checkable="checkable"
      :cascade="cascade"
      :show-line="showLine"
      :dark="dark"
      :expand-on-row-click="expandOnRowClick"
      :expanded-values="currentExpandedValues"
      :loadData="loadData"
      @update-expanded="onUpdateExpanded"
      @on-expand="onExpand"
      @on-node-click="onNodeClick">
      <template #label="slotProps">
        <slot name="label" v-bind="slotProps" />
      </template>

      <template #expand="slotProps">
        <slot name="expand" v-bind="slotProps" />
      </template>

      <template #collapse="slotProps">
        <slot name="collapse" v-bind="slotProps" />
      </template>

      <template #leaf-icon="slotProps">
        <slot name="leaf-icon" v-bind="slotProps" />
      </template>
    </TreeNode>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import TreeNode from "./TreeNode.vue";
import type { TreeEmits, TreeNodeType, TreeProps } from "./types";

// 废弃警告：提示用户迁移到新类型
if (import.meta.env.DEV) {
  console.warn(
    '[ui/Tree] 此组件已废弃，建议迁移到 common/Tree。\n' +
    '- 类型 TreeNodeType 已废弃，请使用 TreeSelectNode\n' +
    '- 字段映射: value → id, label → name\n' +
    '- 导入路径: import { TreeSelectNode } from \'@/framework/types/tree\''
  );
}

type TreeNodeValue = TreeNodeType["value"];

const emit = defineEmits<TreeEmits>();
const props = withDefaults(defineProps<TreeProps>(), {
  cascade: false,
  checkable: false,
  dark: false,
  data: () => [],
  expandOnRowClick: false,
  loadData: undefined,
  modelValue: () => [],
  multiple: false,
  showLine: false,
});

// 存储所有预设选中的节点值
const preSelectedValues = ref<TreeNodeValue[]>([]);
const expandedValues = ref<TreeNodeValue[]>([]);
const currentExpandedValues = computed(() => props.expandedValue ?? expandedValues.value);

// 递归查找所有预设选中的节点
const findPreSelectedNodes = (nodes: TreeNodeType[]) => {
  nodes.forEach((node) => {
    if (node.selected && !preSelectedValues.value.includes(node.value)) {
      preSelectedValues.value.push(node.value);
    }
    if (node.children && node.children.length > 0) {
      findPreSelectedNodes(node.children);
    }
  });
};

const areSameValues = (left: TreeNodeValue[], right: TreeNodeValue[]) => {
  return left.length === right.length && left.every((value, index) => value === right[index]);
};

// 合并 modelValue 和预设选中的值
const selectedValues = computed(() => {
  const uniqueValues = new Set([...props.modelValue, ...preSelectedValues.value]);
  return Array.from(uniqueValues);
});

const onUpdateExpanded = (node: TreeNodeType, expanded: boolean) => {
  if (node.value === undefined) {
    return;
  }

  if (expanded && !currentExpandedValues.value.includes(node.value)) {
    const nextValues = [...currentExpandedValues.value, node.value];
    expandedValues.value = nextValues;
    emit("update:expandedValue", nextValues);
  }

  if (!expanded) {
    const nextValues = currentExpandedValues.value.filter((value) => value !== node.value);
    expandedValues.value = nextValues;
    emit("update:expandedValue", nextValues);
  }
};

// 在组件挂载时初始化预设选中的节点
onMounted(() => {
  findPreSelectedNodes(props.data);
  // 如果有预设选中的节点，通知父组件更新
  if (preSelectedValues.value.length > 0) {
    emit("update:modelValue", selectedValues.value);
  }
});

// 观察数据变化，更新预设选中的节点
watch(
  () => props.data,
  () => {
    const previousPreSelectedValues = [...preSelectedValues.value];
    preSelectedValues.value = [];
    findPreSelectedNodes(props.data);
    if (!areSameValues(previousPreSelectedValues, preSelectedValues.value)) {
      emit("update:modelValue", selectedValues.value);
    }
  },
  { deep: true }
);

// 递归获取所有子节点的值
const getAllChildrenValues = (node: TreeNodeType): TreeNodeValue[] => {
  let values: TreeNodeValue[] = [];
  if (node.children && node.children.length > 0) {
    node.children.forEach((child: TreeNodeType) => {
      values.push(child.value);
      values = values.concat(getAllChildrenValues(child));
    });
  }
  return values;
};

// 递归查找父节点
const findParentNodes = (
  nodes: TreeNodeType[],
  targetValue: TreeNodeValue,
  parent?: TreeNodeType
): TreeNodeType[] => {
  let parents: TreeNodeType[] = [];
  for (const node of nodes) {
    if (node.children && node.children.length > 0) {
      if (node.children.some((child: TreeNodeType) => child.value === targetValue)) {
        if (parent) {
          parents.push(parent);
        }
        parents.push(node);
        return parents;
      }
      const childParents = findParentNodes(node.children, targetValue, node);
      if (childParents.length > 0) {
        if (parent) {
          parents.push(parent);
        }
        parents = parents.concat(childParents);
        return parents;
      }
    }
  }
  return parents;
};

// 检查父节点的所有子节点是否都被选中
const areAllChildrenSelected = (node: TreeNodeType, selectedValues: TreeNodeValue[]): boolean => {
  if (!node.children || node.children.length === 0) {
    return true;
  }
  return node.children.every((child: TreeNodeType) => {
    if (child.children && child.children.length > 0) {
      return areAllChildrenSelected(child, selectedValues);
    }
    return selectedValues.includes(child.value);
  });
};

const onExpand = (node: TreeNodeType) => emit("on-expand", node);

const onNodeClick = (node: TreeNodeType) => {
  if (!props.checkable) {
    const index = selectedValues.value.indexOf(node.value);
    let updatedValues: TreeNodeValue[];

    if (index === -1) {
      if (!props.multiple) {
        updatedValues = [node.value];
        preSelectedValues.value = []; // 单选模式下清除预设选中
      } else {
        updatedValues = [...selectedValues.value, node.value];
      }
    } else {
      updatedValues = selectedValues.value.filter((v) => v !== node.value);
    }

    emit("update:modelValue", updatedValues);
    emit("on-node-click", node);
    return;
  }

  let updatedValues = [...selectedValues.value];
  const index = updatedValues.indexOf(node.value);

  if (!props.cascade) {
    if (index === -1) {
      if (!props.multiple) {
        updatedValues = [node.value];
        preSelectedValues.value = []; // 单选模式下清除预设选中
      } else {
        updatedValues = [...updatedValues, node.value];
      }
    } else {
      updatedValues.splice(index, 1);
    }
  } else {
    if (index === -1) {
      // 当节点被选中时
      updatedValues.push(node.value);

      // 添加所有子节点
      const childrenValues = getAllChildrenValues(node);
      childrenValues.forEach((value) => {
        if (!updatedValues.includes(value)) {
          updatedValues.push(value);
        }
      });

      // 检查父节点状态
      const parentNodes = findParentNodes(props.data, node.value);
      parentNodes.forEach((parent) => {
        if (
          areAllChildrenSelected(parent, updatedValues) &&
          !updatedValues.includes(parent.value)
        ) {
          updatedValues.push(parent.value);
        }
      });
    } else {
      // 当节点取消选中时
      // 移除当前节点
      updatedValues.splice(index, 1);

      // 移除所有子节点
      const childrenValues = getAllChildrenValues(node);
      updatedValues = updatedValues.filter((value) => !childrenValues.includes(value));

      // 移除父节点
      const parentNodes = findParentNodes(props.data, node.value);
      parentNodes.forEach((parent) => {
        const parentIndex = updatedValues.indexOf(parent.value);
        if (parentIndex !== -1) {
          updatedValues.splice(parentIndex, 1);
        }
      });
    }
  }

  emit("update:modelValue", updatedValues);
  emit("on-node-click", node);
};
</script>
