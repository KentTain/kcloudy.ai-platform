<script setup lang="ts">
/**
 * OrganizationSelect - 组织选择器主入口组件
 *
 * Popover 下拉选择框，显示已选组织（Badge 标签，溢出折叠）
 * 支持 Popover 快速搜索和 Dialog 完整选择
 */

import { ref, computed, watch, onMounted } from 'vue'
import { Search, X, ChevronDown, Building2 } from '@lucide/vue'
import { Badge, Input, Skeleton } from '@/components'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import type { OrganizationItem } from '../people-select/types'
import {
  fetchOrganizationDetails,
  searchOrganizations,
} from '../people-select/service'
import OrganizationSelectDialog from './OrganizationSelectDialog.vue'

interface Props {
  /** 已选中的组织 ID 列表（v-model） */
  modelValue?: string[]
  /** 占位文本 */
  placeholder?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的组织 ID 列表 */
  disabledIds?: string[]
  /** 最大显示标签数量（溢出折叠） */
  maxTagCount?: number
  /** 弹窗标题 */
  dialogTitle?: string
  /** 确认按钮文本 */
  confirmText?: string
  /** 自定义样式 */
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  placeholder: '选择组织',
  disabled: false,
  multiple: true,
  disabledIds: () => [],
  maxTagCount: 3,
  dialogTitle: '选择组织',
  confirmText: '确定',
  class: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  'change': [orgIds: string[], orgs: OrganizationItem[]]
}>()

// ========== 状态 ==========

const popoverOpen = ref(false)
const dialogOpen = ref(false)
const searchKeyword = ref('')
const searchLoading = ref(false)
const searchResults = ref<OrganizationItem[]>([])

// 已选组织详情缓存
const selectedOrgsMap = ref<Map<string, OrganizationItem>>(new Map())

// 已选组织列表
const selectedOrgs = computed<OrganizationItem[]>(() => {
  const result: OrganizationItem[] = []
  for (const orgId of props.modelValue) {
    const org = selectedOrgsMap.value.get(orgId)
    if (org) {
      result.push(org)
    }
  }
  return result
})

// 显示的标签（溢出折叠）
const displayOrgs = computed(() => {
  return selectedOrgs.value.slice(0, props.maxTagCount)
})

// 隐藏的组织数量
const hiddenCount = computed(() => {
  return Math.max(0, selectedOrgs.value.length - props.maxTagCount)
})

// ========== 搜索 ==========

let searchTimer: ReturnType<typeof setTimeout> | null = null

async function handleSearch(keyword: string) {
  searchKeyword.value = keyword

  if (searchTimer) clearTimeout(searchTimer)

  if (!keyword.trim()) {
    searchResults.value = []
    return
  }

  searchTimer = setTimeout(async () => {
    searchLoading.value = true
    try {
      const result = await searchOrganizations({ keyword, page: 1, page_size: 20 })
      searchResults.value = result.items
    } catch (error) {
      console.error('Search failed:', error)
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

// ========== 选择操作 ==========

// 禁用的组织 ID 集合
const disabledIdSet = computed(() => new Set(props.disabledIds))

// 判断组织是否已选中
function isSelected(orgId: string): boolean {
  return props.modelValue.includes(orgId)
}

// 切换组织选中
function toggleOrg(orgId: string, org: OrganizationItem) {
  if (props.disabled || disabledIdSet.value.has(orgId)) return

  let newIds: string[]

  if (isSelected(orgId)) {
    newIds = props.modelValue.filter(id => id !== orgId)
    selectedOrgsMap.value.delete(orgId)
  } else {
    if (!props.multiple) {
      // 单选模式：清空之前的选择
      selectedOrgsMap.value.clear()
      newIds = [orgId]
    } else {
      newIds = [...props.modelValue, orgId]
    }
    selectedOrgsMap.value.set(orgId, org)
  }

  emit('update:modelValue', newIds)
  emit('change', newIds, Array.from(selectedOrgsMap.value.values()))
}

// 移除已选组织
function removeOrg(orgId: string) {
  if (props.disabled) return

  const newIds = props.modelValue.filter(id => id !== orgId)
  selectedOrgsMap.value.delete(orgId)
  emit('update:modelValue', newIds)
  emit('change', newIds, Array.from(selectedOrgsMap.value.values()))
}

// 清空所有
function clearAll(event: MouseEvent) {
  event.stopPropagation()
  selectedOrgsMap.value.clear()
  emit('update:modelValue', [])
  emit('change', [], [])
}

// 打开完整选择弹窗
function openDialog() {
  popoverOpen.value = false
  dialogOpen.value = true
}

// 处理弹窗确认
function handleDialogConfirm(orgIds: string[], orgs: OrganizationItem[]) {
  // 更新缓存
  orgs.forEach(org => {
    selectedOrgsMap.value.set(org.id, org)
  })
  emit('update:modelValue', orgIds)
  emit('change', orgIds, orgs)
}

// ========== 加载组织详情 ==========

async function loadSelectedOrgs() {
  for (const orgId of props.modelValue) {
    if (!selectedOrgsMap.value.has(orgId)) {
      const org = await fetchOrganizationDetails(orgId)
      if (org) {
        selectedOrgsMap.value.set(orgId, org)
      }
    }
  }
}

// 监听 modelValue 变化，加载组织详情
watch(
  () => props.modelValue,
  () => {
    loadSelectedOrgs()
  },
  { immediate: true }
)

onMounted(() => {
  loadSelectedOrgs()
})
</script>

<template>
  <div :class="cn('relative', props.class)">
    <!-- 主选择器 -->
    <Popover v-model:open="popoverOpen">
      <PopoverTrigger as-child>
        <button
          type="button"
          :disabled="disabled"
          :class="cn(
            'flex items-center gap-2 w-full min-h-10 px-3 py-2 text-left text-sm',
            'border rounded-md bg-background',
            'hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            selectedOrgs.length === 0 && 'text-muted-foreground'
          )"
        >
          <!-- 已选组织标签 -->
          <template v-if="selectedOrgs.length > 0">
            <div class="flex flex-wrap gap-1 flex-1">
              <Badge
                v-for="org in displayOrgs"
                :key="org.id"
                variant="secondary"
                class="gap-1 pr-1"
              >
                <span class="max-w-[100px] truncate">
                  {{ org.name }}
                </span>
                <button
                  type="button"
                  class="ml-0.5 hover:bg-muted-foreground/20 rounded-sm"
                  @click.stop="removeOrg(org.id)"
                >
                  <X class="h-3 w-3" />
                </button>
              </Badge>
              <Badge
                v-if="hiddenCount > 0"
                variant="secondary"
                class="cursor-pointer"
                @click.stop="openDialog"
              >
                +{{ hiddenCount }}
              </Badge>
            </div>
            <button
              type="button"
              class="p-1 hover:bg-muted rounded"
              @click.stop="clearAll"
            >
              <X class="h-4 w-4 text-muted-foreground" />
            </button>
          </template>
          <template v-else>
            <span class="flex-1">{{ placeholder }}</span>
          </template>
          <ChevronDown class="h-4 w-4 text-muted-foreground shrink-0" />
        </button>
      </PopoverTrigger>

      <PopoverContent
        class="w-80 p-0"
        align="start"
      >
        <!-- 搜索框 -->
        <div class="p-2 border-b">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="searchKeyword"
              placeholder="搜索组织..."
              class="pl-9 h-9"
              @update:model-value="handleSearch"
            />
          </div>
        </div>

        <!-- 搜索结果 -->
        <div class="max-h-60 overflow-y-auto">
          <div v-if="searchLoading" class="p-3 space-y-2">
            <Skeleton class="h-10 w-full" />
            <Skeleton class="h-10 w-full" />
            <Skeleton class="h-10 w-full" />
          </div>
          <div v-else-if="searchKeyword && searchResults.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            未找到匹配的组织
          </div>
          <div v-else-if="searchKeyword && searchResults.length > 0">
            <button
              v-for="org in searchResults"
              :key="org.id"
              type="button"
              :class="cn(
                'flex items-center gap-3 w-full px-3 py-2 text-left hover:bg-muted transition-colors',
                disabledIdSet.has(org.id) && 'opacity-50 cursor-not-allowed'
              )"
              :disabled="disabledIdSet.has(org.id)"
              @click="toggleOrg(org.id, org)"
            >
              <Building2 class="h-5 w-5 text-muted-foreground shrink-0" />
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">
                  {{ org.name }}
                </div>
                <div v-if="org.tree_names" class="text-xs text-muted-foreground truncate">
                  {{ org.tree_names }}
                </div>
              </div>
              <Badge v-if="isSelected(org.id)" variant="default" class="text-xs">
                已选
              </Badge>
            </button>
          </div>
          <div v-else class="p-2">
            <button
              type="button"
              class="flex items-center justify-center gap-2 w-full py-3 text-sm text-muted-foreground hover:bg-muted rounded-md transition-colors"
              @click="openDialog"
            >
              <Building2 class="h-4 w-4" />
              从组织树选择
            </button>
          </div>
        </div>
      </PopoverContent>
    </Popover>

    <!-- 完整选择弹窗 -->
    <OrganizationSelectDialog
      v-model:open="dialogOpen"
      v-model="modelValue"
      :multiple="multiple"
      :disabled-ids="disabledIds"
      :title="dialogTitle"
      :confirm-text="confirmText"
      @confirm="handleDialogConfirm"
    />
  </div>
</template>
