<script setup lang="ts">
/**
 * OrganizationTree 组织树组件
 * 支持单选和多选模式
 */
import { computed, ref, watch } from 'vue'
import { CheckboxTree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'
import { useTreeData } from '@/framework/composables/useTreeData'
import type { Organization } from '@/iam/types'

interface Props {
  organizations: Organization[]
  modelValue: string | string[]
  mode?: 'single' | 'multiple'
  defaultExpandLevel?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'single',
  defaultExpandLevel: 99,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
  'node-click': [node: { id: string; data?: Organization }]
}>()

// 使用 useTreeData 转换组织数据
const { treeData, selectedIds } = useTreeData<Organization, TreeSelectNode>({
  source: computed(() => props.organizations),
  modelValue: computed(() => {
    if (props.mode === 'single') {
      return typeof props.modelValue === 'string' && props.modelValue ? [props.modelValue] : []
    }
    return Array.isArray(props.modelValue) ? props.modelValue : []
  }),
  mode: props.mode,
})

// 扁平化组织列表用于查找
function flattenOrganizations(depts: Organization[]): Organization[] {
  return depts.flatMap(d => [d, ...flattenOrganizations(d.children || [])])
}

// 根据 ID 查找组织
function findOrgById(id: string): Organization | undefined {
  const flatOrgs = flattenOrganizations(props.organizations)
  return flatOrgs.find(d => d.id === id)
}

// 处理节点选择变化
const handleNodeSelect = (value: (string | number)[]) => {
  if (props.mode === 'single') {
    const selected = value.length > 0 ? String(value[value.length - 1]) : ''
    emit('update:modelValue', selected)
    const org = findOrgById(selected)
    emit('node-click', { id: selected, data: org })
  } else {
    emit('update:modelValue', value as string[])
  }
}
</script>

<template>
  <CheckboxTree
    :data="treeData"
    v-model="selectedIds"
    :disabled="disabled"
    :default-expand-level="defaultExpandLevel"
    searchable
    placeholder="搜索组织名称"
    @update:model-value="handleNodeSelect"
  />
</template>
