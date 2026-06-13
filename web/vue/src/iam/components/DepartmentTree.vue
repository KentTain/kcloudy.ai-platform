<script setup lang="ts">
/**
 * DepartmentTree 部门树组件
 * 支持单选和多选模式
 */
import { computed, ref, watch } from 'vue'
import { CheckboxTree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'
import { useTreeData } from '@/framework/composables/useTreeData'
import type { Department } from '@/iam/types'

interface Props {
  departments: Department[]
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
  'node-click': [node: { id: string; data?: Department }]
}>()

// 使用 useTreeData 转换部门数据
const { treeData, selectedIds } = useTreeData<Department, TreeSelectNode>({
  source: () => props.departments,
  modelValue: () => {
    if (props.mode === 'single') {
      return typeof props.modelValue === 'string' && props.modelValue ? [props.modelValue] : []
    }
    return Array.isArray(props.modelValue) ? props.modelValue : []
  },
  mode: props.mode,
})

// 扁平化部门列表用于查找
function flattenDepartments(depts: Department[]): Department[] {
  return depts.flatMap(d => [d, ...flattenDepartments(d.children || [])])
}

// 根据 ID 查找部门
function findDeptById(id: string): Department | undefined {
  const flatDepts = flattenDepartments(props.departments)
  return flatDepts.find(d => d.id === id)
}

// 处理节点选择变化
const handleNodeSelect = (value: (string | number)[]) => {
  if (props.mode === 'single') {
    const selected = value.length > 0 ? String(value[value.length - 1]) : ''
    emit('update:modelValue', selected)
    const dept = findDeptById(selected)
    emit('node-click', { id: selected, data: dept })
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
    placeholder="搜索部门名称"
    @update:model-value="handleNodeSelect"
  />
</template>
