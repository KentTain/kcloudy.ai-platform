<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import CheckboxTree from '@/components/CheckboxTree.vue'
import type { TreeNode } from '@/components/CheckboxTree.vue'
import type { Permission } from '@/iam/types'

interface Props {
  permissions: Permission[]
  modelValue: string[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const treeData = computed<TreeNode[]>(() => {
  const resourceMap = new Map<string, TreeNode>()

  props.permissions.forEach(perm => {
    if (!resourceMap.has(perm.resource)) {
      resourceMap.set(perm.resource, {
        id: `resource-${perm.resource}`,
        name: perm.resource,
        children: [],
      })
    }

    const resourceNode = resourceMap.get(perm.resource)!
    resourceNode.children!.push({
      id: perm.id,
      name: perm.name,
    })
  })

  return Array.from(resourceMap.values())
})

const selectedIds = ref<string[]>([...props.modelValue])

watch(
  () => props.modelValue,
  (newVal) => {
    selectedIds.value = [...newVal]
  },
)

const handleUpdate = (value: (string | number)[]) => {
  // 只保留权限节点 ID（过滤掉 resource 节点）
  const permissionIds = value.filter(id => !String(id).startsWith('resource-'))
  emit('update:modelValue', permissionIds as string[])
}
</script>

<template>
  <CheckboxTree
    :data="treeData"
    v-model="selectedIds"
    :disabled="disabled"
    :default-expand-level="1"
    searchable
    placeholder="搜索权限名称"
    @update:model-value="handleUpdate"
  />
</template>