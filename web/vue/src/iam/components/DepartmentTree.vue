<script setup lang="ts">
/**
 * DepartmentTree 部门树组件
 * 用于展示组织架构的树形结构，支持节点选择、搜索过滤
 */
import { computed, ref, watch } from "vue";
import { createDebounce } from "@/framework/composables/useDebouncedSearch";
import type { Department } from "@/iam/types";

interface Props {
  departments: Department[];
  modelValue: string | string[];
  mode?: "single" | "multiple";
  defaultExpandLevel?: number;
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  mode: "single",
  defaultExpandLevel: 1,
  disabled: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string | string[]];
  "node-click": [node: TreeNode];
  "check-change": [nodes: TreeNode[]];
}>();

const filterText = ref("");
const debouncedFilterText = ref("");

// 防抖搜索优化
const debounceFilter = createDebounce((value: string) => {
  debouncedFilterText.value = value;
}, 300);

watch(filterText, (newVal) => {
  debounceFilter(newVal);
});

interface TreeNode {
  id: string;
  label: string;
  children?: TreeNode[];
  data?: Department;
}

const transformToTreeData = (departments: Department[]): TreeNode[] => {
  return departments.map((dept) => ({
    id: dept.id,
    label: dept.name,
    children: dept.children ? transformToTreeData(dept.children) : undefined,
    data: dept,
  }));
};

const treeData = computed<TreeNode[]>(() => {
  return transformToTreeData(props.departments);
});

const filteredTreeData = computed<TreeNode[]>(() => {
  if (!debouncedFilterText.value.trim()) {
    return treeData.value;
  }

  const keyword = debouncedFilterText.value.toLowerCase();

  const filterNode = (nodes: TreeNode[]): TreeNode[] => {
    const result: TreeNode[] = [];

    nodes.forEach((node) => {
      const labelMatch = node.label?.toLowerCase().includes(keyword);
      const childrenMatch = node.children && filterNode(node.children).length > 0;

      if (labelMatch) {
        result.push(node);
      } else if (childrenMatch) {
        result.push({
          ...node,
          children: filterNode(node.children || []),
        });
      }
    });

    return result;
  };

  return filterNode(treeData.value);
});

const currentKey = ref<string | string[]>(
  typeof props.modelValue === "string" ? props.modelValue : ""
);
const checkedKeys = ref<string[]>(
  Array.isArray(props.modelValue) ? props.modelValue : []
);

watch(
  () => props.modelValue,
  (newVal) => {
    if (props.mode === "single") {
      currentKey.value = typeof newVal === "string" ? newVal : "";
    } else {
      checkedKeys.value = Array.isArray(newVal) ? newVal : [];
    }
  }
);

const handleNodeClick = (data: TreeNode) => {
  if (props.mode === "single") {
    emit("update:modelValue", data.id);
    emit("node-click", data);
  }
};

const handleCheck = (_data: TreeNode, { checkedNodes }: { checkedNodes: TreeNode[] }) => {
  if (props.mode === "multiple") {
    const selectedIds = checkedNodes.map((node) => node.id);
    emit("update:modelValue", selectedIds);
    emit("check-change", checkedNodes);
  }
};

const filterNode = (value: string, data: TreeNode): boolean => {
  if (!value) return true;
  return data.label?.toLowerCase().includes(value.toLowerCase()) || false;
};

defineExpose({
  treeData,
  filteredTreeData,
  filterText,
  debouncedFilterText,
});
</script>

<template>
  <div class="department-tree">
    <el-input
      v-model="filterText"
      placeholder="搜索部门名称"
      clearable
      class="department-tree__search"
      :disabled="disabled"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>

    <!-- 单选模式 -->
    <el-tree
      v-if="mode === 'single'"
      ref="treeRef"
      :data="filteredTreeData"
      :props="{
        children: 'children',
        label: 'label',
      }"
      :current-node-key="currentKey"
      node-key="id"
      :default-expand-all="defaultExpandLevel >= 99"
      :expand-on-click-node="false"
      :filter-node-method="filterNode"
      :disabled="disabled"
      highlight-current
      class="department-tree__content"
      @node-click="handleNodeClick"
    />

    <!-- 多选模式 -->
    <el-tree
      v-else
      ref="treeRef"
      :data="filteredTreeData"
      :props="{
        children: 'children',
        label: 'label',
      }"
      show-checkbox
      :default-checked-keys="checkedKeys"
      node-key="id"
      :default-expand-all="defaultExpandLevel >= 99"
      :filter-node-method="filterNode"
      :disabled="disabled"
      class="department-tree__content"
      @check="handleCheck"
    />
  </div>
</template>

<style scoped>
.department-tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.department-tree__search {
  flex-shrink: 0;
}

.department-tree__content {
  flex: 1;
  overflow: auto;
}
</style>
