<script setup lang="ts">
/**
 * PermissionTree 权限树组件
 * 用于角色管理中的权限分配，支持按资源分组的树形结构展示
 */
import { computed, ref, watch } from "vue";
import { createDebounce } from "@/framework/composables/useDebouncedSearch";
import type { Permission } from "@/iam/types";

interface Props {
  permissions: Permission[];
  modelValue: string[];
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
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
  code?: string;
  description?: string;
  children?: TreeNode[];
  isResource?: boolean;
}

const treeData = computed<TreeNode[]>(() => {
  const resourceMap = new Map<string, TreeNode>();

  props.permissions.forEach((perm) => {
    if (!resourceMap.has(perm.resource)) {
      resourceMap.set(perm.resource, {
        id: `resource-${perm.resource}`,
        label: perm.resource,
        isResource: true,
        children: [],
      });
    }

    const resourceNode = resourceMap.get(perm.resource)!;
    resourceNode.children!.push({
      id: perm.id,
      label: perm.name,
      code: perm.code,
      description: perm.description,
    });
  });

  return Array.from(resourceMap.values());
});

const filteredTreeData = computed<TreeNode[]>(() => {
  if (!debouncedFilterText.value.trim()) {
    return treeData.value;
  }

  const keyword = debouncedFilterText.value.toLowerCase();
  const result: TreeNode[] = [];

  treeData.value.forEach((group) => {
    const matchedChildren = group.children?.filter(
      (child) =>
        child.label?.toLowerCase().includes(keyword) ||
        child.code?.toLowerCase().includes(keyword)
    );

    if (matchedChildren && matchedChildren.length > 0) {
      result.push({
        ...group,
        children: matchedChildren,
      });
    }
  });

  return result;
});

const checkedKeys = ref<string[]>([...props.modelValue]);

watch(
  () => props.modelValue,
  (newVal) => {
    checkedKeys.value = [...newVal];
  }
);

const handleCheck = (_data: TreeNode, { checkedNodes }: { checkedNodes: TreeNode[] }) => {
  const selectedIds = checkedNodes
    .filter((node) => !node.isResource)
    .map((node) => node.id);
  emit("update:modelValue", selectedIds);
};

const getCheckedKeysForResource = (resourceId: string): string[] => {
  const group = treeData.value.find((g) => g.id === resourceId);
  if (!group || !group.children) return [];
  return group.children.map((c) => c.id);
};

const filterNode = (value: string, data: TreeNode): boolean => {
  if (!value) return true;
  const keyword = value.toLowerCase();
  return (
    data.label?.toLowerCase().includes(keyword) ||
    data.code?.toLowerCase().includes(keyword) ||
    false
  );
};

defineExpose({
  treeData,
  filteredTreeData,
  filterText,
  debouncedFilterText,
  getCheckedKeysForResource,
});
</script>

<template>
  <div class="permission-tree">
    <el-input
      v-model="filterText"
      placeholder="搜索权限名称"
      clearable
      class="permission-tree__search"
      :disabled="disabled"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>

    <el-tree
      ref="treeRef"
      :data="filteredTreeData"
      :props="{
        children: 'children',
        label: 'label',
      }"
      show-checkbox
      :default-checked-keys="checkedKeys"
      node-key="id"
      :filter-node-method="filterNode"
      :disabled="disabled"
      class="permission-tree__content"
      @check="handleCheck"
    >
      <template #default="{ data }">
        <span class="permission-tree__node">
          <span class="permission-tree__node-label">{{ data.label }}</span>
          <span v-if="data.code" class="permission-tree__node-code">
            ({{ data.code }})
          </span>
          <span v-if="data.description" class="permission-tree__node-desc">
            - {{ data.description }}
          </span>
        </span>
      </template>
    </el-tree>
  </div>
</template>

<style scoped>
.permission-tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.permission-tree__search {
  flex-shrink: 0;
}

.permission-tree__content {
  flex: 1;
  overflow: auto;
}

.permission-tree__node {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.permission-tree__node-label {
  font-weight: 500;
}

.permission-tree__node-code {
  color: var(--color-text-muted, #6b7280);
  font-size: 12px;
}

.permission-tree__node-desc {
  color: var(--color-text-muted, #6b7280);
  font-size: 12px;
}
</style>
