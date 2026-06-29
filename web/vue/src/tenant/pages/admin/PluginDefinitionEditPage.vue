<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, DescriptionList, type DescriptionItem } from '@/components'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormItem,
  FormLabel,
} from '@/components/ui/form'
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

const basicInfoItems = computed<DescriptionItem[]>(() => {
  if (!plugin.value) return []

  return [
    { label: '插件 ID', value: plugin.value.plugin_id },
    { label: '唯一标识', value: plugin.value.plugin_unique_identifier },
    { label: '安装类型', value: plugin.value.install_type },
    { label: '引用次数', value: String(plugin.value.refers) },
  ]
})

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

    <div v-if="loading" class="space-y-6">
      <div class="h-48 animate-pulse rounded-lg bg-muted" />
      <div class="h-32 animate-pulse rounded-lg bg-muted" />
    </div>

    <div v-else-if="plugin" class="space-y-6">
      <!-- 基本信息卡（只读） -->
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <DescriptionList :items="basicInfoItems" :columns="2" bordered data-testid="plugin-basic-info" />
        </CardContent>
      </Card>

      <!-- 状态设置卡 -->
      <Card>
        <CardHeader>
          <CardTitle>状态设置</CardTitle>
        </CardHeader>
        <CardContent>
          <Form class="space-y-4">
            <FormItem>
              <div class="flex items-center space-x-3">
                <FormControl>
                  <Checkbox
                    id="is_recommended"
                    v-model:checked="formData.is_recommended"
                    data-testid="is-recommended-checkbox"
                  />
                </FormControl>
                <FormLabel for="is_recommended" class="cursor-pointer">
                  是否推荐
                </FormLabel>
              </div>
              <p class="mt-1 text-sm text-muted-foreground">
                推荐的插件将在插件市场优先展示
              </p>
            </FormItem>

            <FormItem>
              <div class="flex items-center space-x-3">
                <FormControl>
                  <Checkbox
                    id="is_enabled"
                    v-model:checked="formData.is_enabled"
                    data-testid="is-enabled-checkbox"
                  />
                </FormControl>
                <FormLabel for="is_enabled" class="cursor-pointer">
                  启用状态
                </FormLabel>
              </div>
              <p class="mt-1 text-sm text-muted-foreground">
                禁用后，租户将无法安装此插件
              </p>
            </FormItem>
          </Form>
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
  </AppPage>
</template>
