<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button } from '@/components'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ArrowLeft } from '@lucide/vue'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import { getPluginDefinition, updatePluginDefinition } from '@/tenant/api/plugin'
import type { PluginDefinitionDetail, UpdatePluginDefinitionRequest } from '@/tenant/api/plugin'

const route = useRoute()
const router = useRouter()

const pluginId = computed(() => route.params.id as string)
const loading = ref(false)
const saving = ref(false)
const plugin = ref<PluginDefinitionDetail | null>(null)

// 表单数据
const formData = ref<UpdatePluginDefinitionRequest>({
  is_recommended: false,
  is_enabled: true,
})

// 原始数据（用于检测变更）
const originalData = ref<UpdatePluginDefinitionRequest>({
  is_recommended: false,
  is_enabled: true,
})

// 是否有修改
const hasChanges = computed(() => {
  return (
    formData.value.is_recommended !== originalData.value.is_recommended ||
    formData.value.is_enabled !== originalData.value.is_enabled
  )
})

const loadPluginDetail = async () => {
  loading.value = true
  try {
    const res = await getPluginDefinition(pluginId.value)
    if (res.code === 200 && res.data) {
      plugin.value = res.data
      // 初始化表单数据
      formData.value = {
        is_recommended: res.data.is_recommended,
        is_enabled: res.data.is_enabled,
      }
      originalData.value = { ...formData.value }
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
  router.push(`/admin/plugin-definitions/${pluginId.value}`)
}

const handleCancel = () => {
  router.push(`/admin/plugin-definitions/${pluginId.value}`)
}

const handleSave = async () => {
  if (!hasChanges.value) return

  saving.value = true
  try {
    const res = await updatePluginDefinition(pluginId.value, formData.value)
    if (res.code === 200) {
      notifySuccess('保存成功')
      router.push(`/admin/plugin-definitions/${pluginId.value}`)
    } else {
      notifyError(res.msg || '保存失败')
    }
  } catch (error) {
    notifyError('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPluginDetail()
})
</script>

<template>
  <AppPage title="编辑插件状态" variant="detail">
    <template #actions>
      <Button variant="outline" @click="handleBack" data-testid="back-button">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回详情
      </Button>
    </template>

    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="min-w-0 flex-1 overflow-auto p-1">
        <div v-if="loading" class="space-y-6">
          <div class="h-48 animate-pulse rounded-lg bg-muted" />
          <div class="h-32 animate-pulse rounded-lg bg-muted" />
        </div>

        <div v-else-if="plugin" class="space-y-6 min-w-0">
          <!-- 基本信息卡（只读） -->
          <Card class="min-w-0">
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="grid gap-4 md:grid-cols-2 min-w-0">
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">插件 ID</div>
                  <div class="mt-2 font-medium break-all">{{ plugin.plugin_id }}</div>
                </div>
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">唯一标识</div>
                  <div class="mt-2 font-medium break-all">{{ plugin.plugin_unique_identifier }}</div>
                </div>
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">安装类型</div>
                  <div class="mt-2 font-medium">{{ plugin.install_type }}</div>
                </div>
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">引用次数</div>
                  <div class="mt-2 font-medium">{{ plugin.refers }}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- 状态设置卡 -->
          <Card class="min-w-0">
            <CardHeader>
              <CardTitle>状态设置</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="space-y-6">
                <div class="flex items-center space-x-3">
                  <Checkbox
                    id="is_recommended"
                    v-model:checked="formData.is_recommended"
                    data-testid="is-recommended-checkbox"
                  />
                  <Label for="is_recommended" class="cursor-pointer">
                    是否推荐
                  </Label>
                </div>
                <p class="text-sm text-muted-foreground -mt-4 ml-7">
                  推荐的插件将在插件市场优先展示
                </p>

                <div class="flex items-center space-x-3">
                  <Checkbox
                    id="is_enabled"
                    v-model:checked="formData.is_enabled"
                    data-testid="is-enabled-checkbox"
                  />
                  <Label for="is_enabled" class="cursor-pointer">
                    启用状态
                  </Label>
                </div>
                <p class="text-sm text-muted-foreground -mt-4 ml-7">
                  禁用后，租户将无法安装此插件
                </p>
              </div>
            </CardContent>
          </Card>

          <!-- 操作按钮 -->
          <div class="flex justify-end gap-3">
            <Button variant="outline" @click="handleCancel" data-testid="cancel-button">
              取消
            </Button>
            <Button
              :disabled="!hasChanges || saving"
              @click="handleSave"
              data-testid="save-button"
            >
              {{ saving ? '保存中...' : '保存' }}
            </Button>
          </div>
        </div>

        <div v-else class="text-center py-12 text-muted-foreground">
          插件不存在或已被删除
        </div>
      </div>
    </div>
  </AppPage>
</template>
