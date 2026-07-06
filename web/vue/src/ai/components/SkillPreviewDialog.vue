<script setup lang="ts">
/**
 * SkillPreviewDialog 预览对话框
 *
 * 展示 Skill 文档内容，支持 Markdown 文件预览
 */
import { ref, watch, computed } from 'vue'
import { FileTextIcon } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components'
import { Button, Badge } from '@/components'
import { ScrollArea } from '@/components/ui/scroll-area'
import { previewSkill } from '@/tenant/api/plugin'
import type { RemoteSkillInfo, SkillPreviewResponse } from '@/tenant/api/plugin'

interface Props {
  open: boolean
  skill: RemoteSkillInfo | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const previewData = ref<SkillPreviewResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const selectedDocument = ref<string>('')

// 加载预览数据
const loadPreview = async () => {
  if (!props.skill) return

  loading.value = true
  error.value = null
  previewData.value = null

  try {
    const response = await previewSkill(props.skill.plugin_id)
    if (response.data) {
      previewData.value = response.data
      // 选择第一个文档
      const documents = response.data.documents
      const docKeys = Object.keys(documents)
      if (docKeys.length > 0) {
        selectedDocument.value = docKeys[0]
      }
    } else {
      error.value = response.error || '加载失败'
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '网络错误'
  } finally {
    loading.value = false
  }
}

// 监听打开状态
watch(
  () => props.open,
  (newOpen) => {
    if (newOpen && props.skill) {
      loadPreview()
    } else {
      // 关闭时重置状态
      previewData.value = null
      selectedDocument.value = ''
    }
  }
)

// 当前文档内容
const currentContent = computed(() => {
  if (!previewData.value || !selectedDocument.value) return ''
  return previewData.value.documents[selectedDocument.value] || ''
})

// 文档列表
const documentList = computed(() => {
  if (!previewData.value) return []
  return Object.keys(previewData.value.documents)
})
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-4xl max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <FileTextIcon class="w-5 h-5" />
          {{ skill?.name || 'Skill 预览' }}
        </DialogTitle>
      </DialogHeader>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="text-muted-foreground">加载中...</div>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="flex-1 flex items-center justify-center">
        <div class="text-destructive">{{ error }}</div>
      </div>

      <!-- 预览内容 -->
      <div v-else-if="previewData" class="flex-1 min-h-0 flex flex-col gap-4">
        <!-- Skill 信息 -->
        <div class="flex items-start gap-3 pb-3 border-b">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <h3 class="text-lg font-semibold">{{ previewData.name }}</h3>
              <Badge :variant="previewData.skill_type === 'knowledge' ? 'default' : 'secondary'">
                {{ previewData.skill_type }}
              </Badge>
            </div>
            <p v-if="previewData.description" class="text-sm text-muted-foreground">
              {{ previewData.description }}
            </p>
          </div>
        </div>

        <!-- 文档选择 -->
        <div v-if="documentList.length > 1" class="flex gap-2 flex-wrap">
          <Button
            v-for="doc in documentList"
            :key="doc"
            :variant="selectedDocument === doc ? 'default' : 'outline'"
            size="sm"
            @click="selectedDocument = doc"
          >
            {{ doc }}
          </Button>
        </div>

        <!-- 文档内容 -->
        <ScrollArea class="flex-1 min-h-0 border rounded-lg">
          <div class="p-4">
            <pre v-if="currentContent" class="whitespace-pre-wrap text-sm font-mono">{{ currentContent }}</pre>
            <div v-else class="text-muted-foreground text-center py-8">
              无文档内容
            </div>
          </div>
        </ScrollArea>
      </div>
    </DialogContent>
  </Dialog>
</template>
