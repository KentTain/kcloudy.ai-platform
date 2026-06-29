<script setup lang="ts">
/**
 * PeopleDisplay - 人员详情卡片
 *
 * Popover 卡片展示用户详情：头像、姓名、用户名、组织、邮箱
 */

import { ref, computed, watch } from 'vue'
import { Mail, Building2, User } from '@lucide/vue'
import {
  Skeleton,
} from '@/components'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import type { UserItem } from './types'
import { fetchUserDetails } from './service'
import PeopleAvatar from './PeopleAvatar.vue'

interface Props {
  /** 用户 ID */
  userId?: string
  /** 用户对象（如果已有数据，避免重复请求） */
  user?: UserItem
  /** 是否禁用 Popover（仅显示内容） */
  disabled?: boolean
  /** 自定义触发器样式 */
  triggerClass?: string
  /** 自定义内容样式 */
  contentClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  userId: undefined,
  user: undefined,
  disabled: false,
  triggerClass: undefined,
  contentClass: undefined,
})

// ========== 状态 ==========

const loading = ref(false)
const userData = ref<UserItem | null>(null)

// 实际显示的用户数据
const displayUser = computed(() => {
  return props.user || userData.value
})

// 是否有数据
const hasData = computed(() => !!displayUser.value)

// ========== 加载用户详情 ==========

async function loadUser() {
  if (props.user) {
    userData.value = null
    return
  }

  if (!props.userId) {
    userData.value = null
    return
  }

  loading.value = true
  try {
    const user = await fetchUserDetails(props.userId)
    userData.value = user
  } catch (error) {
    console.error('Failed to load user details:', error)
    userData.value = null
  } finally {
    loading.value = false
  }
}

// 监听 userId 变化
watch(
  () => props.userId,
  () => {
    if (!props.user) {
      loadUser()
    }
  },
  { immediate: true }
)

// 监听 user 变化
watch(
  () => props.user,
  () => {
    if (props.user) {
      userData.value = null
    } else {
      loadUser()
    }
  }
)
</script>

<template>
  <!-- 禁用模式：仅显示内容 -->
  <div
    v-if="disabled"
    :class="cn('inline-flex items-center gap-2', triggerClass)"
  >
    <PeopleAvatar
      v-if="displayUser"
      :id="displayUser.id"
      :username="displayUser.username"
      :avatar="displayUser.avatar"
      size="sm"
    />
    <span v-if="displayUser" class="text-sm font-medium">
      {{ displayUser.nickname || displayUser.username }}
    </span>
  </div>

  <!-- Popover 模式 -->
  <Popover v-else>
    <PopoverTrigger as-child>
      <button
        type="button"
        :class="cn(
          'inline-flex items-center gap-2 rounded-md hover:bg-muted transition-colors',
          triggerClass
        )"
      >
        <slot :user="displayUser" :loading="loading">
          <PeopleAvatar
            v-if="displayUser"
            :id="displayUser.id"
            :username="displayUser.username"
            :avatar="displayUser.avatar"
            size="sm"
          />
          <span v-if="displayUser" class="text-sm font-medium">
            {{ displayUser.nickname || displayUser.username }}
          </span>
        </slot>
      </button>
    </PopoverTrigger>

    <PopoverContent
      :class="cn('w-72 p-0', contentClass)"
      align="start"
    >
      <!-- 加载中 -->
      <div v-if="loading" class="p-4">
        <div class="flex items-center gap-3 mb-4">
          <Skeleton class="h-12 w-12 rounded-full" />
          <div class="flex-1 space-y-2">
            <Skeleton class="h-4 w-24" />
            <Skeleton class="h-3 w-32" />
          </div>
        </div>
        <Skeleton class="h-3 w-full mb-2" />
        <Skeleton class="h-3 w-3/4" />
      </div>

      <!-- 用户信息 -->
      <div v-else-if="hasData && displayUser" class="p-4">
        <!-- 头部：头像 + 名称 -->
        <div class="flex items-center gap-3 mb-4">
          <PeopleAvatar
            :id="displayUser.id"
            :username="displayUser.username"
            :avatar="displayUser.avatar"
            size="lg"
          />
          <div class="flex-1 min-w-0">
            <div class="text-base font-semibold truncate">
              {{ displayUser.nickname || displayUser.username }}
            </div>
            <div class="text-sm text-muted-foreground truncate">
              @{{ displayUser.username }}
            </div>
          </div>
        </div>

        <!-- 详细信息 -->
        <div class="space-y-2 text-sm">
          <!-- 邮箱 -->
          <div v-if="displayUser.email" class="flex items-center gap-2 text-muted-foreground">
            <Mail class="h-4 w-4 shrink-0" />
            <a
              :href="`mailto:${displayUser.email}`"
              class="hover:text-primary truncate"
            >
              {{ displayUser.email }}
            </a>
          </div>

          <!-- 组织 -->
          <div v-if="displayUser.org_tree_names" class="flex items-center gap-2 text-muted-foreground">
            <Building2 class="h-4 w-4 shrink-0" />
            <span class="truncate">{{ displayUser.org_tree_names }}</span>
          </div>

          <!-- 状态 -->
          <div class="flex items-center gap-2 text-muted-foreground">
            <User class="h-4 w-4 shrink-0" />
            <span>
              {{ displayUser.status === 'active' ? '正常' : '停用' }}
            </span>
          </div>
        </div>

        <!-- 操作按钮（可扩展） -->
        <div v-if="$slots.actions" class="mt-4 pt-3 border-t">
          <slot name="actions" :user="displayUser" />
        </div>
      </div>

      <!-- 无数据 -->
      <div v-else class="p-4 text-center text-muted-foreground text-sm">
        暂无用户信息
      </div>
    </PopoverContent>
  </Popover>
</template>
