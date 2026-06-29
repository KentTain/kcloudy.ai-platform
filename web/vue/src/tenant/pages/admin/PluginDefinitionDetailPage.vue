<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Badge, Skeleton, DescriptionList, type DescriptionItem } from '@/components'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  ArrowLeft,
  Pencil,
  Copy,
  ChevronDown,
  ChevronUp,
  Check,
  Loader2,
} from '@lucide/vue'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import { getPluginDefinition, updatePluginDefinition } from '@/tenant/api/plugin'
import type { PluginDefinitionDetail } from '@/tenant/api/plugin'

const route = useRoute()
const router = useRouter()

const pluginId = computed(() => route.params.id as string)
const loading = ref(false)
const plugin = ref<PluginDefinitionDetail | null>(null)
const declarationExpanded = ref(true)
const copied = ref(false)

// 编辑状态
const editingRecommended = ref(false)
const editingEnabled = ref(false)
const savingRecommended = ref(false)
const savingEnabled = ref(false)

const loadPluginDetail = async () => {
  loading.value = true
  try {
    const res = await getPluginDefinition(pluginId.value)
    if (res.code === 200 && res.data) {
      plugin.value = res.data
    } else {
      notifyError('加载插件详情失败')
    }
  } catch (error) {
    notifyError('加载插件详情失败')
  } finally {
    loading.value = false
  }
}

const handleBack = () => {
  router.push('/admin/plugin-definitions')
}

const handleEditRecommended = () => {
  editingRecommended.value = true
}

const handleCancelEditRecommended = () => {
  editingRecommended.value = false
}

const handleSaveRecommended = async () => {
  if (!plugin.value) return

  savingRecommended.value = true
  try {
    const newRecommended = !plugin.value.is_recommended
    const res = await updatePluginDefinition(plugin.value.id, {
      is_recommended: newRecommended,
    })
    if (res.code === 200 && res.data) {
      plugin.value = { ...plugin.value, is_recommended: newRecommended }
      notifySuccess(newRecommended ? '已设为推荐' : '已取消推荐')
      editingRecommended.value = false
    } else {
      notifyError('更新失败')
    }
  } catch (error) {
    notifyError('更新失败')
  } finally {
    savingRecommended.value = false
  }
}

const handleEditEnabled = () => {
  editingEnabled.value = true
}

const handleCancelEditEnabled = () => {
  editingEnabled.value = false
}

const handleSaveEnabled = async () => {
  if (!plugin.value) return

  savingEnabled.value = true
  try {
    const newEnabled = !plugin.value.is_enabled
    const res = await updatePluginDefinition(plugin.value.id, {
      is_enabled: newEnabled,
    })
    if (res.code === 200 && res.data) {
      plugin.value = { ...plugin.value, is_enabled: newEnabled }
      notifySuccess(newEnabled ? '已启用' : '已禁用')
      editingEnabled.value = false
    } else {
      notifyError('更新失败')
    }
  } catch (error) {
    notifyError('更新失败')
  } finally {
    savingEnabled.value = false
  }
}

const handleCopyDeclaration = async () => {
  if (!plugin.value) return

  try {
    await navigator.clipboard.writeText(JSON.stringify(plugin.value.declaration, null, 2))
    copied.value = true
    notifySuccess('已复制到剪贴板')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    notifyError('复制失败')
  }
}

const toggleDeclaration = () => {
  declarationExpanded.value = !declarationExpanded.value
}

const descriptionItems = computed<DescriptionItem[]>(() => {
  if (!plugin.value) return []

  return [
    { label: '插件 ID', value: plugin.value.plugin_id },
    { label: '唯一标识', value: plugin.value.plugin_unique_identifier },
    { label: '安装类型', value: plugin.value.install_type },
    { label: '引用次数', value: String(plugin.value.refers) },
    {
      label: '是否推荐',
      value: plugin.value.is_recommended ? '是' : '否',
      type: 'badge',
      badgeVariant: plugin.value.is_recommended ? 'default' : 'secondary',
    },
    {
      label: '启用状态',
      value: plugin.value.is_enabled ? '启用' : '禁用',
      type: 'badge',
      badgeVariant: plugin.value.is_enabled ? 'default' : 'secondary',
    },
    {
      label: '创建时间',
      value: plugin.value.created_at ? new Date(plugin.value.created_at).toLocaleString() : '-',
    },
    {
      label: '更新时间',
      value: plugin.value.updated_at ? new Date(plugin.value.updated_at).toLocaleString() : '-',
    },
  ]
})

onMounted(() => {
  loadPluginDetail()
})
</script>

<template>
  <AppPage title="插件详情" variant="detail">
    <template #actions>
      <Button variant="outline" @click="handleBack" data-testid="back-button">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回列表
      </Button>
    </template>

    <div v-if="loading" class="space-y-6">
      <Skeleton class="h-48 w-full" />
      <Skeleton class="h-64 w-full" />
    </div>

    <div v-else-if="plugin" class="space-y-6">
      <!-- 基本信息卡 -->
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <DescriptionList :items="descriptionItems" :columns="2" bordered data-testid="plugin-info">
            <template #label-{label}>
              <span class="font-medium text-muted-foreground">{{ label }}</span>
            </template>

            <!-- 是否推荐 编辑 -->
            <template #value-是否推荐>
              <div class="flex items-center gap-2">
                <Badge :variant="plugin.is_recommended ? 'default' : 'secondary'">
                  {{ plugin.is_recommended ? '是' : '否' }}
                </Badge>
                <div v-if="editingRecommended" class="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    :disabled="savingRecommended"
                    @click="handleSaveRecommended"
                  >
                    <Loader2 v-if="savingRecommended" class="mr-1 h-3 w-3 animate-spin" />
                    <Check v-else class="mr-1 h-3 w-3" />
                    确认
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    :disabled="savingRecommended"
                    @click="handleCancelEditRecommended"
                  >
                    取消
                  </Button>
                </div>
                <Button
                  v-else
                  size="sm"
                  variant="ghost"
                  @click="handleEditRecommended"
                  data-testid="edit-recommended-button"
                >
                  <Pencil class="h-3 w-3" />
                </Button>
              </div>
            </template>

            <!-- 启用状态 编辑 -->
            <template #value-启用状态>
              <div class="flex items-center gap-2">
                <Badge :variant="plugin.is_enabled ? 'default' : 'secondary'">
                  {{ plugin.is_enabled ? '启用' : '禁用' }}
                </Badge>
                <div v-if="editingEnabled" class="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    :disabled="savingEnabled"
                    @click="handleSaveEnabled"
                  >
                    <Loader2 v-if="savingEnabled" class="mr-1 h-3 w-3 animate-spin" />
                    <Check v-else class="mr-1 h-3 w-3" />
                    确认
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    :disabled="savingEnabled"
                    @click="handleCancelEditEnabled"
                  >
                    取消
                  </Button>
                </div>
                <Button
                  v-else
                  size="sm"
                  variant="ghost"
                  @click="handleEditEnabled"
                  data-testid="edit-enabled-button"
                >
                  <Pencil class="h-3 w-3" />
                </Button>
              </div>
            </template>
          </DescriptionList>
        </CardContent>
      </Card>

      <!-- 声明内容卡 -->
      <Card>
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle>声明内容</CardTitle>
            <div class="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                @click="handleCopyDeclaration"
                data-testid="copy-declaration-button"
              >
                <Check v-if="copied" class="mr-1 h-4 w-4" />
                <Copy v-else class="mr-1 h-4 w-4" />
                {{ copied ? '已复制' : '复制' }}
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="toggleDeclaration"
                data-testid="toggle-declaration-button"
              >
                <ChevronDown v-if="declarationExpanded" class="mr-1 h-4 w-4" />
                <ChevronUp v-else class="mr-1 h-4 w-4" />
                {{ declarationExpanded ? '折叠' : '展开' }}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent v-if="declarationExpanded">
          <pre
            class="overflow-auto rounded-md bg-muted p-4 text-sm"
            data-testid="declaration-content"
          >{{ JSON.stringify(plugin.declaration, null, 2) }}</pre>
        </CardContent>
      </Card>
    </div>

    <div v-else class="text-center py-12 text-muted-foreground">
      插件不存在或已被删除
    </div>
  </AppPage>
</template>
