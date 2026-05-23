<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import * as z from 'zod'
import { useTenantStore } from '@/iam/stores/tenant'
import type { CreateTenantParams, UpdateTenantParams } from '@/iam/types'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import DateInput from '@/components/DateInput.vue'

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

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    const submitData: CreateTenantParams & UpdateTenantParams = {
      ...values,
      expired_at: expiredAt.value,
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

onMounted(async () => {
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

      <div class="flex gap-2">
        <Button type="submit" :disabled="loading">
          {{ isEdit ? '保存' : '创建' }}
        </Button>
        <Button variant="outline" @click="handleCancel">取消</Button>
      </div>
    </form>
  </AppPage>
</template>