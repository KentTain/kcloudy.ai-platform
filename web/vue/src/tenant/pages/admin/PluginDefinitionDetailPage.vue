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
} from '@lucide/vue'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import { getPluginDefinition } from '@/tenant/api/plugin'
import type { PluginDefinitionDetail } from '@/tenant/api/plugin'

const route = useRoute()
const router = useRouter()

const pluginId = computed(() => route.params.id as string)
const loading = ref(false)
const plugin = ref<PluginDefinitionDetail | null>(null)
const declarationExpanded = ref(true)
const copied = ref(false)

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

const handleEdit = () => {
  router.push(`/admin/plugin-definitions/${pluginId.value}/edit`)
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
            <template #item="{ item }">
              <!-- 是否推荐 -->
              <div v-if="item.label === '是否推荐'" class="flex items-center gap-2">
                <Badge :variant="plugin.is_recommended ? 'default' : 'secondary'">
                  {{ plugin.is_recommended ? '是' : '否' }}
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  @click="handleEdit"
                  data-testid="edit-recommended-button"
                >
                  <Pencil class="h-3.5 w-3.5" />
                </Button>
              </div>
              <!-- 启用状态 -->
              <div v-else-if="item.label === '启用状态'" class="flex items-center gap-2">
                <Badge :variant="plugin.is_enabled ? 'default' : 'secondary'">
                  {{ plugin.is_enabled ? '启用' : '禁用' }}
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  @click="handleEdit"
                  data-testid="edit-enabled-button"
                >
                  <Pencil class="h-3.5 w-3.5" />
                </Button>
              </div>
              <!-- 其他字段默认显示 -->
              <template v-else>
                <span v-if="item.type === 'badge'">
                  <Badge :variant="item.badgeVariant || 'default'">{{ item.value || '--' }}</Badge>
                </span>
                <span v-else>{{ item.value || '--' }}</span>
              </template>
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
