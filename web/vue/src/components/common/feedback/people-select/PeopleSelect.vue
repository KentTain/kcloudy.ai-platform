<script setup lang="ts">
/**
 * PeopleSelect - 人员选择器主入口组件
 *
 * Popover 下拉搜索框，显示已选人员（Badge 标签，溢出折叠）
 * 支持 Popover 搜索和 Dialog 完整选择
 */

import { ref, computed, watch, onMounted } from 'vue'
import { Search, X, ChevronDown, Users } from '@lucide/vue'
import { Badge, Input, Skeleton } from '@/components'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import type { UserItem } from './types'
import { fetchUserDetails, searchUsers } from './service'
import PeopleAvatar from './PeopleAvatar.vue'
import PeopleSelectDialog from './PeopleSelectDialog.vue'

interface Props {
  /** 已选中的用户 ID 列表（v-model） */
  modelValue?: string[]
  /** 占位文本 */
  placeholder?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的用户 ID 列表 */
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
  placeholder: '选择人员',
  disabled: false,
  multiple: true,
  disabledIds: () => [],
  maxTagCount: 3,
  dialogTitle: '选择人员',
  confirmText: '确定',
  class: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  'change': [userIds: string[], users: UserItem[]]
}>()

// ========== 状态 ==========

const popoverOpen = ref(false)
const dialogOpen = ref(false)
const searchKeyword = ref('')
const searchLoading = ref(false)
const searchResults = ref<UserItem[]>([])

// 已选用户详情缓存
const selectedUsersMap = ref<Map<string, UserItem>>(new Map())

// 已选用户列表
const selectedUsers = computed<UserItem[]>(() => {
  const result: UserItem[] = []
  for (const userId of props.modelValue) {
    const user = selectedUsersMap.value.get(userId)
    if (user) {
      result.push(user)
    }
  }
  return result
})

// 显示的标签（溢出折叠）
const displayUsers = computed(() => {
  return selectedUsers.value.slice(0, props.maxTagCount)
})

// 隐藏的用户数量
const hiddenCount = computed(() => {
  return Math.max(0, selectedUsers.value.length - props.maxTagCount)
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
      const result = await searchUsers({ keyword, page: 1, page_size: 20 })
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

// 禁用的用户 ID 集合
const disabledIdSet = computed(() => new Set(props.disabledIds))

// 判断用户是否已选中
function isSelected(userId: string): boolean {
  return props.modelValue.includes(userId)
}

// 切换用户选中
function toggleUser(userId: string, user: UserItem) {
  if (props.disabled || disabledIdSet.value.has(userId)) return

  let newIds: string[]

  if (isSelected(userId)) {
    newIds = props.modelValue.filter(id => id !== userId)
    selectedUsersMap.value.delete(userId)
  } else {
    if (!props.multiple) {
      // 单选模式：清空之前的选择
      selectedUsersMap.value.clear()
      newIds = [userId]
    } else {
      newIds = [...props.modelValue, userId]
    }
    selectedUsersMap.value.set(userId, user)
  }

  emit('update:modelValue', newIds)
  emit('change', newIds, Array.from(selectedUsersMap.value.values()))
}

// 移除已选用户
function removeUser(userId: string) {
  if (props.disabled) return

  const newIds = props.modelValue.filter(id => id !== userId)
  selectedUsersMap.value.delete(userId)
  emit('update:modelValue', newIds)
  emit('change', newIds, Array.from(selectedUsersMap.value.values()))
}

// 清空所有
function clearAll(event: MouseEvent) {
  event.stopPropagation()
  selectedUsersMap.value.clear()
  emit('update:modelValue', [])
  emit('change', [], [])
}

// 打开完整选择弹窗
function openDialog() {
  popoverOpen.value = false
  dialogOpen.value = true
}

// 处理弹窗确认
function handleDialogConfirm(userIds: string[], users: UserItem[]) {
  // 更新缓存
  users.forEach(user => {
    selectedUsersMap.value.set(user.id, user)
  })
  emit('update:modelValue', userIds)
  emit('change', userIds, users)
}

// ========== 加载用户详情 ==========

async function loadSelectedUsers() {
  for (const userId of props.modelValue) {
    if (!selectedUsersMap.value.has(userId)) {
      const user = await fetchUserDetails(userId)
      if (user) {
        selectedUsersMap.value.set(userId, user)
      }
    }
  }
}

// 监听 modelValue 变化，加载用户详情
watch(
  () => props.modelValue,
  () => {
    loadSelectedUsers()
  },
  { immediate: true }
)

onMounted(() => {
  loadSelectedUsers()
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
            selectedUsers.length === 0 && 'text-muted-foreground'
          )"
        >
          <!-- 已选人员标签 -->
          <template v-if="selectedUsers.length > 0">
            <div class="flex flex-wrap gap-1 flex-1">
              <Badge
                v-for="user in displayUsers"
                :key="user.id"
                variant="secondary"
                class="gap-1 pr-1"
              >
                <span class="max-w-[100px] truncate">
                  {{ user.nickname || user.username }}
                </span>
                <button
                  type="button"
                  class="ml-0.5 hover:bg-muted-foreground/20 rounded-sm"
                  @click.stop="removeUser(user.id)"
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
              placeholder="搜索用户..."
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
            未找到匹配的用户
          </div>
          <div v-else-if="searchKeyword && searchResults.length > 0">
            <button
              v-for="user in searchResults"
              :key="user.id"
              type="button"
              :class="cn(
                'flex items-center gap-3 w-full px-3 py-2 text-left hover:bg-muted transition-colors',
                disabledIdSet.has(user.id) && 'opacity-50 cursor-not-allowed'
              )"
              :disabled="disabledIdSet.has(user.id)"
              @click="toggleUser(user.id, user)"
            >
              <PeopleAvatar
                :id="user.id"
                :username="user.username"
                :avatar="user.avatar"
                size="sm"
              />
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">
                  {{ user.nickname || user.username }}
                </div>
                <div v-if="user.org_tree_names" class="text-xs text-muted-foreground truncate">
                  {{ user.org_tree_names }}
                </div>
              </div>
              <Badge v-if="isSelected(user.id)" variant="default" class="text-xs">
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
              <Users class="h-4 w-4" />
              从组织树选择
            </button>
          </div>
        </div>
      </PopoverContent>
    </Popover>

    <!-- 完整选择弹窗 -->
    <PeopleSelectDialog
      v-model:open="dialogOpen"
      :model-value="modelValue"
      :multiple="multiple"
      :disabled-ids="disabledIds"
      :title="dialogTitle"
      :confirm-text="confirmText"
      @update:model-value="$emit('update:modelValue', $event)"
      @confirm="handleDialogConfirm"
    />
  </div>
</template>
