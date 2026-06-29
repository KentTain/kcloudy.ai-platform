<script setup lang="ts">
/**
 * PeopleSelectView - 人员选择视图
 *
 * 左右布局：左侧组织人员树 + 右侧已选人员列表
 * 使用 useOrgPeopleTree composable 和 OrgTreeNode/UserTreeNode 组件
 */

import { ref, computed, watch, onMounted } from 'vue'
import { Search, X, Users } from '@lucide/vue'
import { Input, Badge, Skeleton, Button } from '@/components'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { UserItem } from './types'
import { useOrgPeopleTree } from './useOrgPeopleTree'
import OrgTreeNode from './OrgTreeNode.vue'
import UserTreeNode from './UserTreeNode.vue'
import PeopleAvatar from './PeopleAvatar.vue'

interface Props {
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的用户 ID 列表 */
  disabledIds?: string[]
  /** 已选中的用户 ID 列表（v-model） */
  modelValue?: string[]
  /** 默认展开层级 */
  defaultExpandLevel?: number
}

const props = withDefaults(defineProps<Props>(), {
  multiple: true,
  disabledIds: () => [],
  modelValue: () => [],
  defaultExpandLevel: 1,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
  'select': [users: UserItem[]]
}>()

// ========== Composable ==========

const modelValueRef = computed(() => props.modelValue)
const disabledIdsRef = computed(() => props.disabledIds)

const {
  flatVisibleNodes,
  checkedUserIds,
  loadingOrgIds,
  loading,
  initTree,
  toggleOrgExpand,
  toggleUserCheck,
  toggleOrgCheck,
  clearChecked,
  getCheckedUserIds,
} = useOrgPeopleTree({
  multiple: props.multiple,
  modelValue: modelValueRef,
  disabledIds: disabledIdsRef,
  defaultExpandLevel: props.defaultExpandLevel,
})

// ========== 搜索功能 ==========

const searchKeyword = ref('')
const searchResults = ref<UserItem[]>([])
const searchLoading = ref(false)
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
      const { searchUsers } = await import('./service')
      const result = await searchUsers({ keyword, page: 1, page_size: 50 })
      searchResults.value = result.items
    } catch (error) {
      console.error('Search failed:', error)
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

// 是否显示搜索结果
const showSearchResults = computed(() => searchKeyword.value.trim() !== '')

// ========== 已选人员 ==========

// 用户详情缓存（用于显示已选人员信息）
const selectedUsersMap = ref<Map<string, UserItem>>(new Map())

// 已选用户列表
const selectedUsers = computed<UserItem[]>(() => {
  const result: UserItem[] = []
  for (const userId of checkedUserIds.value) {
    const user = selectedUsersMap.value.get(userId)
    if (user) {
      result.push(user)
    }
  }
  return result
})

// 加载已选用户详情
async function loadSelectedUsers() {
  const userIds = Array.from(checkedUserIds.value)
  if (userIds.length === 0) return

  const { fetchUserDetails } = await import('./service')
  for (const userId of userIds) {
    if (!selectedUsersMap.value.has(userId)) {
      const user = await fetchUserDetails(userId)
      if (user) {
        selectedUsersMap.value.set(userId, user)
      }
    }
  }
}

// 监听选中变化，加载用户详情
watch(checkedUserIds, () => {
  loadSelectedUsers()
  emit('update:modelValue', getCheckedUserIds())
}, { deep: true })

// ========== 事件处理 ==========

function handleToggleExpand(orgId: string) {
  toggleOrgExpand(orgId)
}

function handleToggleUserCheck(userId: string) {
  toggleUserCheck(userId)
}

function handleToggleOrgCheck(orgId: string) {
  toggleOrgCheck(orgId)
}

function handleRemoveSelected(userId: string) {
  toggleUserCheck(userId)
}

function handleClearAll() {
  clearChecked()
}

// 判断用户是否禁用
const disabledIdSet = computed(() => new Set(props.disabledIds))

// ========== 初始化 ==========

onMounted(() => {
  initTree()
  loadSelectedUsers()
})
</script>

<template>
  <div class="flex h-[460px] border rounded-lg overflow-hidden">
    <!-- 左侧：组织人员树 -->
    <div class="w-1/2 border-r flex flex-col bg-muted/20">
      <!-- 搜索框 -->
      <div class="p-3 border-b">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            v-model="searchKeyword"
            placeholder="搜索用户..."
            class="pl-9 h-9 text-sm"
            @update:model-value="handleSearch"
          />
        </div>
      </div>

      <!-- 树内容 -->
      <ScrollArea class="flex-1">
        <!-- 搜索结果 -->
        <div v-if="showSearchResults" class="p-2">
          <div v-if="searchLoading" class="py-4 text-center">
            <Skeleton class="h-6 w-full mb-2" />
            <Skeleton class="h-6 w-full mb-2" />
            <Skeleton class="h-6 w-full" />
          </div>
          <div v-else-if="searchResults.length === 0" class="py-8 text-center text-muted-foreground text-sm">
            未找到匹配的用户
          </div>
          <div v-else>
            <UserTreeNode
              v-for="node in searchResults.map(user => ({
                id: user.id,
                name: user.nickname || user.username,
                type: 'user' as const,
                parent_id: user.org_id || null,
                tree_level: 0,
                tree_leaf: true,
                expanded: false,
                checkState: checkedUserIds.has(user.id) ? 'checked' as const : 'unchecked' as const,
                data: user,
              }))"
              :key="node.id"
              :node="node"
              :checkable="true"
              :disabled="disabledIdSet.has(node.id)"
              class="mb-1"
              @toggle-check="handleToggleUserCheck"
            />
          </div>
        </div>

        <!-- 组织树 -->
        <div v-else class="p-2">
          <div v-if="loading" class="space-y-2">
            <Skeleton v-for="i in 5" :key="i" class="h-8 w-full" />
          </div>
          <div v-else-if="flatVisibleNodes.length === 0" class="py-8 text-center text-muted-foreground text-sm">
            暂无组织数据
          </div>
          <template v-else>
            <template v-for="node in flatVisibleNodes" :key="node.id">
              <OrgTreeNode
                v-if="node.type === 'org'"
                :node="node"
                :checkable="true"
                :loading="loadingOrgIds.has(node.id)"
                @toggle-expand="handleToggleExpand"
                @toggle-check="handleToggleOrgCheck"
              />
              <UserTreeNode
                v-else
                :node="node"
                :checkable="true"
                :disabled="disabledIdSet.has(node.id)"
                @toggle-check="handleToggleUserCheck"
              />
            </template>
          </template>
        </div>
      </ScrollArea>
    </div>

    <!-- 右侧：已选人员 -->
    <div class="w-1/2 flex flex-col">
      <!-- 头部 -->
      <div class="flex items-center justify-between px-4 py-3 border-b">
        <span class="text-sm font-medium">
          已选人员
          <Badge v-if="selectedUsers.length > 0" variant="secondary" class="ml-2">
            {{ selectedUsers.length }}
          </Badge>
        </span>
        <Button
          v-if="selectedUsers.length > 0"
          variant="ghost"
          size="sm"
          class="h-7 px-2 text-xs text-muted-foreground"
          @click="handleClearAll"
        >
          清空
        </Button>
      </div>

      <!-- 已选列表 -->
      <ScrollArea class="flex-1">
        <div v-if="selectedUsers.length === 0" class="flex flex-col items-center justify-center h-full text-muted-foreground">
          <Users class="h-12 w-12 mb-3 opacity-40" />
          <p class="text-sm">暂无选中人员</p>
        </div>
        <div v-else class="p-2">
          <div
            v-for="user in selectedUsers"
            :key="user.id"
            class="flex items-center gap-3 px-3 py-2 mb-1 rounded-md hover:bg-muted/50 group"
          >
            <PeopleAvatar
              :id="user.id"
              :username="user.username"
              :avatar="user.avatar"
              size="sm"
              class="shrink-0"
            />
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">
                {{ user.nickname || user.username }}
              </div>
              <div v-if="user.org_tree_names" class="text-xs text-muted-foreground truncate">
                {{ user.org_tree_names }}
              </div>
            </div>
            <button
              type="button"
              class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-muted rounded"
              @click="handleRemoveSelected(user.id)"
            >
              <X class="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
