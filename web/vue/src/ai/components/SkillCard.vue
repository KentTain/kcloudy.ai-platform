<script setup lang="ts">
/**
 * SkillCard 卡片组件
 *
 * 展示 Skill 的基本信息，包括名称、类型、标签、统计信息
 * 支持安装和预览操作
 */
import { DownloadIcon, EyeIcon } from 'lucide-vue-next'
import { Button, Badge } from '@/components'
import { Card } from '@/components/ui/card'
import type { RemoteSkillInfo } from '@/tenant/api/plugin'

interface Props {
  skill: RemoteSkillInfo
  isInstalled: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  install: [skill: RemoteSkillInfo]
  preview: [skill: RemoteSkillInfo]
}>()

const handleInstall = () => {
  emit('install', props.skill)
}

const handlePreview = () => {
  emit('preview', props.skill)
}

const formatDownloads = (count: number | null): string => {
  if (count === null) return '0'
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  return String(count)
}
</script>

<template>
  <Card class="p-4">
    <div class="flex flex-col gap-3">
      <!-- 头部：名称和作者 -->
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <h3 class="text-base font-semibold truncate">{{ skill.name }}</h3>
          <p class="text-sm text-muted-foreground truncate">{{ skill.author }}</p>
        </div>
        <Badge
          data-testid="skill-type-badge"
          :variant="skill.skill_type === 'knowledge' ? 'default' : 'secondary'"
          class="ml-2 shrink-0"
        >
          {{ skill.skill_type }}
        </Badge>
      </div>

      <!-- 描述 -->
      <p v-if="skill.description" class="text-sm text-muted-foreground line-clamp-2">
        {{ skill.description }}
      </p>

      <!-- 标签 -->
      <div v-if="skill.tags.length > 0" class="flex flex-wrap gap-1">
        <Badge
          v-for="tag in skill.tags"
          :key="tag"
          data-testid="skill-tag"
          variant="outline"
          class="text-xs"
        >
          {{ tag }}
        </Badge>
      </div>

      <!-- 统计信息 -->
      <div class="flex items-center gap-3 text-xs text-muted-foreground">
        <div class="flex items-center gap-1">
          <DownloadIcon class="w-3 h-3" />
          <span>{{ formatDownloads(skill.downloads) }}</span>
        </div>
        <span>v{{ skill.version }}</span>
      </div>

      <!-- 操作按钮 -->
      <div class="flex gap-2">
        <Button
          v-if="!isInstalled"
          data-testid="install-button"
          size="sm"
          class="flex-1"
          @click="handleInstall"
        >
          安装
        </Button>
        <div
          v-else
          class="flex-1 text-center text-sm text-muted-foreground py-1.5"
        >
          已安装
        </div>
        <Button
          data-testid="preview-button"
          size="sm"
          variant="outline"
          class="flex-1"
          @click="handlePreview"
        >
          <EyeIcon class="w-4 h-4 mr-1" />
          预览
        </Button>
      </div>
    </div>
  </Card>
</template>
