<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CheckboxTree } from '@/components'
import type { TreeComponentNode } from '@/framework/types/tree'
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

const treeData = computed<TreeComponentNode[]>(() => {
  return props.departments.map(dept => ({
    id: dept.id,
    name: dept.name,
    children: dept.children ? dept.children.map(child => ({
      id: child.id,
      name: child.name,
      children: child.children?.length ? child.children.map(c => ({
        id: c.id,
        name: c.name,
      })) : undefined,
    })) : undefined,
  }))
})

// 单选模式 - 使用数组形式绑定
const selectedIdArray = ref<(string | number)[]>(
  typeof props.modelValue === 'string' && props.modelValue ? [props.modelValue] : [],
)

// 多选模式
const selectedIds = ref<(string | number)[]>(
  Array.isArray(props.modelValue) ? props.modelValue : [],
)

watch(
  () => props.modelValue,
  (newVal) => {
    if (props.mode === 'single') {
      selectedIdArray.value = typeof newVal === 'string' && newVal ? [newVal] : []
    } else {
      selectedIds.value = Array.isArray(newVal) ? newVal : []
    }
  },
)

// 单选时点击节点
const handleNodeSelect = (value: (string | number)[]) => {
  if (props.mode === 'single') {
    const selected = value.length > 0 ? String(value[value.length - 1]) : ''
    emit('update:modelValue', selected)
    // 找到对应的 Department 数据
    const dept = findDeptById(selected)
    emit('node-click', { id: selected, data: dept })
  } else {
    emit('update:modelValue', value as string[])
  }
}

function findDeptById(id: string): Department | undefined {
  const flatDepts = flattenDepartments(props.departments)
  return flatDepts.find(d => d.id === id)
}

function flattenDepartments(depts: Department[]): Department[] {
  return depts.flatMap(d => [d, ...flattenDepartments(d.children || [])])
}
</script>

<template>
  <!-- 单选模式 -->
  <CheckboxTree
    v-if="mode === 'single'"
    :data="treeData"
    v-model="selectedIdArray"
    :disabled="disabled"
    :default-expand-level="defaultExpandLevel"
    searchable
    placeholder="搜索部门名称"
    @update:model-value="handleNodeSelect"
  />

  <!-- 多选模式 -->
  <CheckboxTree
    v-else
    :data="treeData"
    v-model="selectedIds"
    :disabled="disabled"
    :default-expand-level="defaultExpandLevel"
    searchable
    placeholder="搜索部门名称"
    @update:model-value="handleNodeSelect"
  />
</template>