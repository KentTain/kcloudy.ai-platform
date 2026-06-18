<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import * as z from 'zod'
import { useTenantStore } from '@/tenant/stores/tenant'
import type { TenantCreate, TenantUpdate, ResourceConfig } from '@/tenant/types'
import {
  getDatabaseConfigs,
  getStorageConfigs,
  getCacheConfigs,
  getQueueConfigs,
  getPubsubConfigs,
} from '@/tenant/api/resourceConfig'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Input, DateInput, Select } from '@/components'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components'

const route = useRoute()
const router = useRouter()
const tenantStore = useTenantStore()

const isEdit = computed(() => !!route.params.id)
const tenantId = computed(() => route.params.id as string)

const formSchema = toTypedSchema(z.object({
  name: z.string().min(1, '请输入租户名称'),
  code: z.string().min(1, '请输入租户编码'),
  contact_name: z.string().optional(),
  contact_email: z.string().email('请输入有效的邮箱地址').optional().or(z.literal('')),
  contact_phone: z.string().optional(),
  expired_at: z.string().optional(),
}))

const { handleSubmit, setValues } = useForm({
  validationSchema: formSchema,
})

const loading = ref(false)
const expiredAt = ref<string | undefined>(undefined)

// 资源配置选择
const dbConfigId = ref<string | number | null>(null)
const storageConfigId = ref<string | number | null>(null)
const cacheConfigId = ref<string | number | null>(null)
const queueConfigId = ref<string | number | null>(null)
const pubsubConfigId = ref<string | number | null>(null)

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

    databaseConfigs.value = dbRes.data.items ?? []
    storageConfigs.value = storageRes.data.items ?? []
    cacheConfigs.value = cacheRes.data.items ?? []
    queueConfigs.value = queueRes.data.items ?? []
    pubsubConfigs.value = pubsubRes.data.items ?? []

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

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    const submitData: TenantCreate & TenantUpdate = {
      ...values,
      expired_at: expiredAt.value,
      db_config_id: (dbConfigId.value as string) || undefined,
      storage_config_id: (storageConfigId.value as string) || undefined,
      cache_config_id: (cacheConfigId.value as string) || undefined,
      queue_config_id: (queueConfigId.value as string) || undefined,
      pubsub_config_id: (pubsubConfigId.value as string) || undefined,
    }
    if (isEdit.value) {
      await tenantStore.editTenant(tenantId.value, submitData)
    } else {
      await tenantStore.addTenant(submitData)
    }
    router.back()
  } finally {
    loading.value = false
  }
})

const handleCancel = () => {
  router.back()
}

const goToResourceConfig = () => {
  router.push('/admin/resources')
}

onMounted(async () => {
  // 加载资源配置列表
  await loadResourceConfigs()

  if (isEdit.value) {
    await tenantStore.fetchTenant(tenantId.value)
    const tenant = tenantStore.currentTenant
    if (tenant) {
      setValues({
        name: tenant.name,
        code: tenant.code,
        contact_name: tenant.contact_name || '',
        contact_email: tenant.contact_email || '',
        contact_phone: tenant.contact_phone || '',
        expired_at: tenant.expired_at || '',
      })
      expiredAt.value = tenant.expired_at
      // 编辑模式下使用租户已绑定的资源配置
      if (tenant.db_config) dbConfigId.value = tenant.db_config.id
      if (tenant.storage_config) storageConfigId.value = tenant.storage_config.id
      if (tenant.cache_config) cacheConfigId.value = tenant.cache_config.id
      if (tenant.queue_config) queueConfigId.value = tenant.queue_config.id
      if (tenant.pubsub_config) pubsubConfigId.value = tenant.pubsub_config.id
    }
  }
})
</script>

<template>
  <AppPage :title="isEdit ? '编辑租户' : '创建租户'" variant="detail">
    <form @submit="onSubmit" class="max-w-[600px] flex flex-col gap-6">
      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel>租户名称</FormLabel>
          <FormControl>
            <Input v-bind="componentField" :disabled="isEdit" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="code">
        <FormItem>
          <FormLabel>租户编码</FormLabel>
          <FormControl>
            <Input v-bind="componentField" :disabled="isEdit" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="contact_name">
        <FormItem>
          <FormLabel>联系人</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="contact_email">
        <FormItem>
          <FormLabel>联系人邮箱</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="contact_phone">
        <FormItem>
          <FormLabel>联系人电话</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <div class="flex flex-col gap-2">
        <FormLabel>过期时间</FormLabel>
        <DateInput
          v-model="expiredAt"
          type="single"
          placeholder="选择过期时间（不选则永久）"
        />
      </div>

      <!-- 资源配置选择区域 -->
      <div class="flex flex-col gap-4 rounded-md border p-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-medium">资源配置</h3>
          <Button type="button" variant="ghost" size="sm" @click="goToResourceConfig">
            + 创建新配置
          </Button>
        </div>

        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <FormLabel>数据库配置</FormLabel>
            <Select
              v-model="dbConfigId"
              :options="databaseOptions"
              placeholder="选择数据库配置"
              clearable
            />
          </div>

          <div class="flex flex-col gap-2">
            <FormLabel>存储配置</FormLabel>
            <Select
              v-model="storageConfigId"
              :options="storageOptions"
              placeholder="选择存储配置"
              clearable
            />
          </div>

          <div class="flex flex-col gap-2">
            <FormLabel>缓存配置</FormLabel>
            <Select
              v-model="cacheConfigId"
              :options="cacheOptions"
              placeholder="选择缓存配置"
              clearable
            />
          </div>

          <div class="flex flex-col gap-2">
            <FormLabel>队列配置</FormLabel>
            <Select
              v-model="queueConfigId"
              :options="queueOptions"
              placeholder="选择队列配置"
              clearable
            />
          </div>

          <div class="flex flex-col gap-2">
            <FormLabel>发布订阅配置</FormLabel>
            <Select
              v-model="pubsubConfigId"
              :options="pubsubOptions"
              placeholder="选择发布订阅配置"
              clearable
            />
          </div>
        </div>
      </div>

      <div class="flex gap-2">
        <Button type="submit" :disabled="loading">
          {{ isEdit ? '保存' : '创建' }}
        </Button>
        <Button variant="outline" @click="handleCancel">取消</Button>
      </div>
    </form>
  </AppPage>
</template>
