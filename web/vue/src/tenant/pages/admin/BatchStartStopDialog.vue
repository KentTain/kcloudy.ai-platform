<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Button, Badge, Checkbox, Input } from '@/components'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import {
  batchStartPluginInstallations,
  batchStopPluginInstallations,
} from '@/tenant/api/plugin'
import { getTenants } from '@/tenant/api/tenant'
import type { PluginDefinition } from '@/tenant/api/plugin'
import type { Tenant } from '@/tenant/types'

const props = defineProps<{
  plugin: PluginDefinition | null
  open: boolean
  mode: 'start' | 'stop'
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  done: []
}>()

const loading = ref(false)
const submitting = ref(false)
const tenants = ref<Tenant[]>([])
const selectedIds = ref<string[]>([])
const searchKeyword = ref('')

const isStart = computed(() => props.mode === 'start')
const title = computed(() => (isStart.value ? '启动插件' : '停止插件'))
const description = computed(() =>
  isStart.value
    ? `将插件「${props.plugin?.plugin_id}」在选定的租户中启动`
    : `将插件「${props.plugin?.plugin_id}」在选定的租户中停止`
)

const filteredTenants = computed(() => {
  if (!searchKeyword.value) return tenants.value
  const kw = searchKeyword.value.toLowerCase()
  return tenants.value.filter(
    (t) => t.name.toLowerCase().includes(kw) || t.code.toLowerCase().includes(kw)
  )
})

const selectedCount = computed(() => selectedIds.value.length)

const toggleSelectAll = () => {
  if (selectedCount.value === filteredTenants.value.length && filteredTenants.value.length > 0) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredTenants.value.map((t) => t.id)
  }
}

const toggleTenant = (id: string) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) {
    selectedIds.value = [...selectedIds.value, id]
  } else {
    selectedIds.value = selectedIds.value.filter((i) => i !== id)
  }
}

const isSelected = (id: string) => selectedIds.value.includes(id)

const loadTenants = async () => {
  loading.value = true
  try {
    const res = await getTenants({ page: 1, page_size: 200, status: 'active' })
    if (res.data) {
      tenants.value = res.data
    }
  } catch {
    notifyError('加载租户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (selectedIds.value.length === 0) {
    notifyError('请选择至少一个租户')
    return
  }
  if (!props.plugin) return

  submitting.value = true
  try {
    const apiFn = isStart.value ? batchStartPluginInstallations : batchStopPluginInstallations
    const res = await apiFn({
      plugin_id: props.plugin.plugin_id,
      tenant_ids: selectedIds.value,
    })
    if (res.data) {
      const { success, failed } = res.data
      const parts: string[] = []
      if (success.length > 0) parts.push(`成功 ${success.length} 个`)
      if (failed.length > 0) parts.push(`失败 ${failed.length} 个`)
      notifySuccess(`${isStart.value ? '启动' : '停止'}完成：${parts.join('，')}`)
    }
    emit('update:open', false)
    emit('done')
  } catch {
    notifyError(isStart.value ? '启动失败' : '停止失败')
  } finally {
    submitting.value = false
  }
}

watch(
  () => props.open,
  (val) => {
    if (val) {
      selectedIds.value = []
      searchKeyword.value = ''
      loadTenants()
    }
  }
)
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[520px]">
      <DialogHeader>
        <DialogTitle>{{ title }}</DialogTitle>
        <DialogDescription>{{ description }}</DialogDescription>
      </DialogHeader>

      <div class="space-y-3">
        <!-- 搜索 -->
        <Input
          v-model="searchKeyword"
          placeholder="搜索租户名称或编码"
        />

        <!-- 操作栏 -->
        <div class="flex items-center justify-between text-sm">
          <span class="text-muted-foreground">
            已选 {{ selectedCount }} 个租户
          </span>
          <Button variant="ghost" size="sm" @click="toggleSelectAll">
            {{ selectedCount === filteredTenants.length && filteredTenants.length > 0 ? '取消全选' : '全选' }}
          </Button>
        </div>

        <!-- 租户列表 -->
        <ScrollArea class="h-[300px] rounded-md border">
          <div v-if="loading" class="flex items-center justify-center py-8 text-muted-foreground">
            加载中...
          </div>
          <div v-else-if="filteredTenants.length === 0" class="flex items-center justify-center py-8 text-muted-foreground">
            无匹配租户
          </div>
          <div v-else class="p-2 space-y-1">
            <div
              v-for="tenant in filteredTenants"
              :key="tenant.id"
              class="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted cursor-pointer"
              @click="toggleTenant(tenant.id)"
            >
              <Checkbox :checked="isSelected(tenant.id)" />
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">{{ tenant.name }}</div>
                <div class="text-xs text-muted-foreground">{{ tenant.code }}</div>
              </div>
              <Badge :variant="tenant.status === 'active' ? 'default' : 'secondary'" class="shrink-0">
                {{ tenant.status === 'active' ? '活跃' : '停用' }}
              </Badge>
            </div>
          </div>
        </ScrollArea>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="emit('update:open', false)">取消</Button>
        <Button :disabled="selectedCount === 0 || submitting" @click="handleSubmit">
          {{ submitting ? (isStart ? '启动中...' : '停止中...') : `确认${isStart ? '启动' : '停止'}（${selectedCount} 个租户）` }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
