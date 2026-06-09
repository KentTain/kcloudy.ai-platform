<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTenantStore } from '@/tenant/stores/tenant'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button } from '@/components/ui/button'
import { DescriptionList, type DescriptionItem } from '@/components/common'
import { Pencil, ShieldCheck, ShieldOff } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const tenantStore = useTenantStore()

const tenantId = computed(() => route.params.id as string)
const loading = ref(false)

const loadTenantDetail = async () => {
  loading.value = true
  try {
    await tenantStore.fetchTenant(tenantId.value)
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  router.push(`/tenants/${tenantId.value}/edit`)
}

const handleBack = () => {
  router.back()
}

const handleActivate = async () => {
  await tenantStore.activate(tenantId.value)
  await loadTenantDetail()
}

const handleDeactivate = async () => {
  await tenantStore.deactivate(tenantId.value)
  await loadTenantDetail()
}

const descriptionItems = computed<DescriptionItem[]>(() => {
  const tenant = tenantStore.currentTenant
  if (!tenant) return []

  return [
    { label: '租户名称', value: tenant.name },
    { label: '租户编码', value: tenant.code },
    { label: '联系人', value: tenant.contact_name },
    { label: '联系人邮箱', value: tenant.contact_email },
    { label: '联系人电话', value: tenant.contact_phone },
    {
      label: '状态',
      value: tenant.status === 'active' ? '激活' : '停用',
      type: 'badge',
      badgeVariant: tenant.status === 'active' ? 'default' : 'secondary',
    },
    {
      label: '过期时间',
      value: tenant.expired_at ? new Date(tenant.expired_at).toLocaleString() : '永久',
    },
    { label: '创建时间', value: new Date(tenant.created_at).toLocaleString() },
  ]
})

onMounted(() => {
  loadTenantDetail()
})
</script>

<template>
  <AppPage title="租户详情" variant="detail">
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="handleBack">返回</Button>
        <Button @click="handleEdit">
          <Pencil class="mr-1 h-4 w-4" />
          编辑
        </Button>
        <Button
          v-if="tenantStore.currentTenant?.status === 'inactive'"
          variant="outline"
          @click="handleActivate"
        >
          <ShieldCheck class="mr-1 h-4 w-4" />
          激活
        </Button>
        <Button
          v-if="tenantStore.currentTenant?.status === 'active'"
          variant="outline"
          @click="handleDeactivate"
        >
          <ShieldOff class="mr-1 h-4 w-4" />
          停用
        </Button>
      </div>
    </template>

    <div v-if="loading" class="flex flex-col gap-3">
      <div v-for="n in 4" :key="n" class="h-5">
        <div class="h-5 w-full bg-muted animate-pulse rounded" />
      </div>
    </div>
    <DescriptionList v-else :items="descriptionItems" :columns="2" bordered />
  </AppPage>
</template>
