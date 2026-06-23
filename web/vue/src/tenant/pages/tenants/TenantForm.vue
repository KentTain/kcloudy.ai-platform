<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTenant, createTenant, updateTenant } from '@/tenant/api/tenant'
import {
  getDatabaseConfigs,
  getStorageConfigs,
  getCacheConfigs,
  getQueueConfigs,
  getPubsubConfigs,
} from '@/tenant/api/resourceConfig'
import type { TenantCreate, TenantUpdate, ResourceConfig } from '@/tenant/types'
import { notifySuccess, notifyError } from '@/framework/utils/feedback'
import { Button, Input, Label, Card, Select } from '@/components'
import { ArrowLeft, Save } from '@lucide/vue'
import DateInput from '@/components/common/form/date-input/DateInput.vue'

const route = useRoute()
const router = useRouter()

const tenantId = computed(() => route.params.id as string)
const isEdit = computed(() => !!tenantId.value)
const loading = ref(false)
const saving = ref(false)

// 表单数据
const form = ref({
  name: '',
  code: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
  expired_at: '',
})

// 表单验证错误
const errors = ref<Record<string, string>>({})

// 资源配置选择
const dbConfigId = ref<string | null>(null)
const storageConfigId = ref<string | null>(null)
const cacheConfigId = ref<string | null>(null)
const queueConfigId = ref<string | null>(null)
const pubsubConfigId = ref<string | null>(null)

// 资源配置列表
const databaseConfigs = ref<ResourceConfig[]>([])
const storageConfigs = ref<ResourceConfig[]>([])
const cacheConfigs = ref<ResourceConfig[]>([])
const queueConfigs = ref<ResourceConfig[]>([])
const pubsubConfigs = ref<ResourceConfig[]>([])

/**
 * 将配置列表按 is_default 排序（默认配置排在最前），并转换为 Select 组件的 options
 */
function toSortedOptions(configs: ResourceConfig[]) {
  const sorted = [...configs].sort((a, b) => {
    if (a.is_default && !b.is_default) return -1
    if (!a.is_default && b.is_default) return 1
    return 0
  })
  return sorted.map((config) => ({
    label: config.is_default ? `${config.name}（默认）` : config.name,
    value: config.id,
  }))
}

const databaseOptions = computed(() => toSortedOptions(databaseConfigs.value))
const storageOptions = computed(() => toSortedOptions(storageConfigs.value))
const cacheOptions = computed(() => toSortedOptions(cacheConfigs.value))
const queueOptions = computed(() => toSortedOptions(queueConfigs.value))
const pubsubOptions = computed(() => toSortedOptions(pubsubConfigs.value))

/**
 * 获取默认配置 ID
 */
function getDefaultConfigId(configs: ResourceConfig[]): string | null {
  const defaultConfig = configs.find((c) => c.is_default)
  return defaultConfig?.id ?? null
}

/**
 * 加载所有资源配置列表，并自动选中默认配置
 */
async function loadResourceConfigs() {
  try {
    const [dbRes, storageRes, cacheRes, queueRes, pubsubRes] = await Promise.all([
      getDatabaseConfigs({ page: 1, page_size: 100 }),
      getStorageConfigs({ page: 1, page_size: 100 }),
      getCacheConfigs({ page: 1, page_size: 100 }),
      getQueueConfigs({ page: 1, page_size: 100 }),
      getPubsubConfigs({ page: 1, page_size: 100 }),
    ])

    databaseConfigs.value = dbRes.data ?? []
    storageConfigs.value = storageRes.data ?? []
    cacheConfigs.value = cacheRes.data ?? []
    queueConfigs.value = queueRes.data ?? []
    pubsubConfigs.value = pubsubRes.data ?? []

    // 自动选中默认配置
    dbConfigId.value = getDefaultConfigId(databaseConfigs.value)
    storageConfigId.value = getDefaultConfigId(storageConfigs.value)
    cacheConfigId.value = getDefaultConfigId(cacheConfigs.value)
    queueConfigId.value = getDefaultConfigId(queueConfigs.value)
    pubsubConfigId.value = getDefaultConfigId(pubsubConfigs.value)
  } catch (error) {
    console.error('加载资源配置失败:', error)
  }
}

/**
 * 加载租户详情（编辑模式）
 */
const loadTenant = async () => {
  if (!isEdit.value) return

  loading.value = true
  try {
    const response = await getTenant(tenantId.value)
    if (response.data) {
      const data = response.data
      form.value = {
        name: data.name,
        code: data.code,
        contact_name: data.contact_name || '',
        contact_email: data.contact_email || '',
        contact_phone: data.contact_phone || '',
        expired_at: data.expired_at || '',
      }
      // 编辑模式下使用租户已绑定的资源配置
      if (data.db_config) dbConfigId.value = data.db_config.id
      if (data.storage_config) storageConfigId.value = data.storage_config.id
      if (data.cache_config) cacheConfigId.value = data.cache_config.id
      if (data.queue_config) queueConfigId.value = data.queue_config.id
      if (data.pubsub_config) pubsubConfigId.value = data.pubsub_config.id
    }
  } catch (error) {
    console.error('加载租户详情失败:', error)
    notifyError('加载租户详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 验证表单
 */
const validateForm = (): boolean => {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = '请输入租户名称'
  }

  if (!form.value.code.trim()) {
    errors.value.code = '请输入租户编码'
  } else if (!/^[a-z][a-z0-9_]*$/.test(form.value.code)) {
    errors.value.code = '租户编码必须以小写字母开头，只能包含小写字母、数字和下划线'
  }

  if (form.value.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.contact_email)) {
    errors.value.contact_email = '请输入有效的邮箱地址'
  }

  return Object.keys(errors.value).length === 0
}

/**
 * 保存租户
 */
const handleSave = async () => {
  if (!validateForm()) return

  saving.value = true
  try {
    if (isEdit.value) {
      const updatePayload: TenantUpdate = {
        name: form.value.name,
        contact_name: form.value.contact_name || undefined,
        contact_email: form.value.contact_email || undefined,
        contact_phone: form.value.contact_phone || undefined,
        expired_at: form.value.expired_at || undefined,
        db_config_id: dbConfigId.value || undefined,
        storage_config_id: storageConfigId.value || undefined,
        cache_config_id: cacheConfigId.value || undefined,
        queue_config_id: queueConfigId.value || undefined,
        pubsub_config_id: pubsubConfigId.value || undefined,
      }
      await updateTenant(tenantId.value, updatePayload)
      notifySuccess('租户已更新')
    } else {
      const createPayload: TenantCreate = {
        name: form.value.name,
        code: form.value.code,
        contact_name: form.value.contact_name || undefined,
        contact_email: form.value.contact_email || undefined,
        contact_phone: form.value.contact_phone || undefined,
        expired_at: form.value.expired_at || undefined,
        db_config_id: dbConfigId.value || undefined,
        storage_config_id: storageConfigId.value || undefined,
        cache_config_id: cacheConfigId.value || undefined,
        queue_config_id: queueConfigId.value || undefined,
        pubsub_config_id: pubsubConfigId.value || undefined,
      }
      await createTenant(createPayload)
      notifySuccess('租户已创建')
    }
    router.push('/admin/tenants')
  } catch (error: any) {
    console.error('保存租户失败:', error)
    const errorMessage = error?.response?.data?.msg || error?.message || '保存失败'
    notifyError(errorMessage)
  } finally {
    saving.value = false
  }
}

/**
 * 返回列表
 */
const handleBack = () => {
  router.push('/admin/tenants')
}

/**
 * 跳转到资源配置页面
 */
const goToResourceConfig = () => {
  router.push('/admin/resources')
}

onMounted(async () => {
  await loadResourceConfigs()
  await loadTenant()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" @click="handleBack" data-testid="back-button">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold" data-testid="page-title">{{ isEdit ? '编辑租户' : '新增租户' }}</h2>
          <p class="text-muted-foreground mt-1 text-sm">
            {{ isEdit ? '修改租户基本信息和资源配置' : '创建新的租户' }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="handleBack" data-testid="cancel-button">取消</Button>
        <Button :disabled="saving" @click="handleSave" data-testid="save-button">
          <Save class="mr-1 h-4 w-4" />
          {{ saving ? '保存中...' : '保存' }}
        </Button>
      </div>
    </div>

    <!-- 表单区域 -->
    <Card class="flex min-h-0 flex-1 flex-col overflow-auto p-6">
      <div v-if="loading" class="flex flex-col gap-4">
        <div v-for="n in 10" :key="n" class="space-y-2">
          <div class="h-4 w-20 bg-muted animate-pulse rounded" />
          <div class="h-10 w-full bg-muted animate-pulse rounded" />
        </div>
      </div>

      <div v-else class="mx-auto w-full max-w-2xl space-y-6">
        <!-- 基本信息 -->
        <div class="space-y-4">
          <h3 class="text-sm font-medium text-muted-foreground">基本信息</h3>

          <!-- 租户名称 -->
          <div class="space-y-2">
            <Label for="name">租户名称 <span class="text-destructive">*</span></Label>
            <Input
              id="name"
              v-model="form.name"
              placeholder="请输入租户名称"
              data-testid="input-name"
              :class="{ 'border-destructive': errors.name }"
            />
            <p v-if="errors.name" class="text-destructive text-xs">{{ errors.name }}</p>
          </div>

          <!-- 租户编码 -->
          <div class="space-y-2">
            <Label for="code">租户编码 <span class="text-destructive">*</span></Label>
            <Input
              id="code"
              v-model="form.code"
              placeholder="例如: my_company"
              data-testid="input-code"
              :disabled="isEdit"
              :class="{ 'border-destructive': errors.code }"
            />
            <p v-if="errors.code" class="text-destructive text-xs">{{ errors.code }}</p>
            <p v-else class="text-muted-foreground text-xs">
              租户编码只能包含小写字母、数字和下划线，创建后不可修改
            </p>
          </div>
        </div>

        <!-- 联系信息 -->
        <div class="space-y-4">
          <h3 class="text-sm font-medium text-muted-foreground">联系信息</h3>

          <div class="grid gap-4 md:grid-cols-2">
            <!-- 联系人 -->
            <div class="space-y-2">
              <Label for="contact_name">联系人</Label>
              <Input
                id="contact_name"
                v-model="form.contact_name"
                placeholder="请输入联系人姓名"
                data-testid="input-contact-name"
              />
            </div>

            <!-- 联系电话 -->
            <div class="space-y-2">
              <Label for="contact_phone">联系电话</Label>
              <Input
                id="contact_phone"
                v-model="form.contact_phone"
                placeholder="请输入联系电话"
                data-testid="input-contact-phone"
              />
            </div>
          </div>

          <!-- 联系人邮箱 -->
          <div class="space-y-2">
            <Label for="contact_email">联系人邮箱</Label>
            <Input
              id="contact_email"
              v-model="form.contact_email"
              placeholder="请输入联系人邮箱"
              data-testid="input-contact-email"
              :class="{ 'border-destructive': errors.contact_email }"
            />
            <p v-if="errors.contact_email" class="text-destructive text-xs">{{ errors.contact_email }}</p>
          </div>
        </div>

        <!-- 过期时间 -->
        <div class="space-y-2">
          <Label>过期时间</Label>
          <DateInput
            v-model="form.expired_at"
            type="single"
            placeholder="选择过期时间（不选则永久）"
          />
          <p class="text-muted-foreground text-xs">不选择过期时间则表示租户永久有效</p>
        </div>

        <!-- 资源配置 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-medium text-muted-foreground">资源配置</h3>
            <Button type="button" variant="ghost" size="sm" @click="goToResourceConfig">
              + 创建新配置
            </Button>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <!-- 数据库配置 -->
            <div class="space-y-2">
              <Label>数据库配置</Label>
              <Select
                v-model="dbConfigId"
                :options="databaseOptions"
                placeholder="选择数据库配置"
                clearable
              />
            </div>

            <!-- 存储配置 -->
            <div class="space-y-2">
              <Label>存储配置</Label>
              <Select
                v-model="storageConfigId"
                :options="storageOptions"
                placeholder="选择存储配置"
                clearable
              />
            </div>

            <!-- 缓存配置 -->
            <div class="space-y-2">
              <Label>缓存配置</Label>
              <Select
                v-model="cacheConfigId"
                :options="cacheOptions"
                placeholder="选择缓存配置"
                clearable
              />
            </div>

            <!-- 队列配置 -->
            <div class="space-y-2">
              <Label>队列配置</Label>
              <Select
                v-model="queueConfigId"
                :options="queueOptions"
                placeholder="选择队列配置"
                clearable
              />
            </div>

            <!-- 发布订阅配置 -->
            <div class="space-y-2">
              <Label>发布订阅配置</Label>
              <Select
                v-model="pubsubConfigId"
                :options="pubsubOptions"
                placeholder="选择发布订阅配置"
                clearable
              />
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
