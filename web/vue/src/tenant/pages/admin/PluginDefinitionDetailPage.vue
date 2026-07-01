<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Badge, Skeleton } from '@/components'
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
  Download,
} from '@lucide/vue'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import { getPluginDefinition } from '@/tenant/api/plugin'
import type { PluginDefinitionDetail } from '@/tenant/api/plugin'
import InstallToTenantsDialog from './InstallToTenantsDialog.vue'

const route = useRoute()
const router = useRouter()

const pluginId = computed(() => route.params.id as string)
const loading = ref(false)
const plugin = ref<PluginDefinitionDetail | null>(null)
const declarationExpanded = ref(true)
const copied = ref(false)

const installDialogOpen = ref(false)

const handleInstallToTenants = () => {
  installDialogOpen.value = true
}

const handleInstalled = () => {
  loadPluginDetail()
}

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

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString()
}

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
      <Button variant="outline" @click="handleInstallToTenants" data-testid="install-to-tenants-button">
        <Download class="mr-1 h-4 w-4" />
        安装到租户
      </Button>
    </template>

    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="min-w-0 flex-1 overflow-auto p-1">
        <div v-if="loading" class="space-y-6">
          <Skeleton class="h-48 w-full" />
          <Skeleton class="h-64 w-full" />
        </div>

        <div v-else-if="plugin" class="space-y-6 min-w-0">
          <!-- 基本信息卡 -->
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
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">是否推荐</div>
                  <div class="mt-2 flex items-center gap-2">
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
                </div>
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">启用状态</div>
                  <div class="mt-2 flex items-center gap-2">
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
                </div>
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">创建时间</div>
                  <div class="mt-2 font-medium">{{ formatDate(plugin.created_at) }}</div>
                </div>
                <div class="rounded-lg border p-4 min-w-0">
                  <div class="text-muted-foreground text-xs">更新时间</div>
                  <div class="mt-2 font-medium">{{ formatDate(plugin.updated_at) }}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- 声明内容卡 -->
          <Card class="min-w-0">
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
                class="overflow-auto rounded-md bg-muted p-4 text-sm max-h-96 whitespace-pre-wrap break-all"
                data-testid="declaration-content"
              >{{ JSON.stringify(plugin.declaration, null, 2) }}</pre>
            </CardContent>
          </Card>
        </div>

        <div v-else class="text-center py-12 text-muted-foreground">
          插件不存在或已被删除
        </div>
      </div>
    </div>
    <InstallToTenantsDialog
      :plugin="plugin"
      :open="installDialogOpen"
      @update:open="installDialogOpen = $event"
      @installed="handleInstalled"
    />
  </AppPage>
</template>
