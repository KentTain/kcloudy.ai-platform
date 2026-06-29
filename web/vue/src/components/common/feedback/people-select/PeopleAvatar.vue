<script setup lang="ts">
/**
 * PeopleAvatar - 人员头像组件
 *
 * 支持通过用户 ID 或用户名显示头像，处理图片加载失败场景。
 */
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { User } from '@lucide/vue'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'

interface Props {
  /** 用户 ID */
  id?: string
  /** 用户名 */
  username?: string
  /** 头像 URL */
  avatar?: string | null
  /** 自定义样式 */
  class?: HTMLAttributes['class']
  /** 头像尺寸 */
  size?: 'sm' | 'default' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  id: undefined,
  username: undefined,
  avatar: undefined,
  class: undefined,
  size: 'default',
})

// 计算头像 URL
const avatarUrl = computed(() => {
  if (props.avatar) {
    return props.avatar
  }
  // 如果没有头像，返回 null，显示默认图标
  return null
})

// 计算显示的首字母
const fallbackText = computed(() => {
  if (props.username) {
    return props.username.charAt(0).toUpperCase()
  }
  return ''
})

// 图片加载错误处理
function handleImageError(event: Event) {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}
</script>

<template>
  <Avatar :class="cn(props.class)" :size="size">
    <AvatarImage
      v-if="avatarUrl"
      :src="avatarUrl"
      :alt="username || 'User avatar'"
      @error="handleImageError"
    />
    <AvatarFallback class="bg-muted text-muted-foreground">
      <slot name="fallback">
        <span v-if="fallbackText" class="text-xs font-medium">{{ fallbackText }}</span>
        <User v-else class="h-4 w-4" />
      </slot>
    </AvatarFallback>
  </Avatar>
</template>
