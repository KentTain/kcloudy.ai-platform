<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import * as z from 'zod'
import { useUserStore } from '@/iam/stores/user'
import type { UserCreate, UserUpdate } from '@/iam/types'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Input } from '@/components'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isEdit = computed(() => !!route.params.id)
const userId = computed(() => route.params.id as string)

const createSchema = toTypedSchema(z.object({
  username: z.string().min(3, '用户名长度为 3-50 个字符').max(50, '用户名长度为 3-50 个字符'),
  password: z.string().min(8, '密码长度为 8-32 个字符').max(32, '密码长度为 8-32 个字符'),
  email: z.string().email('请输入有效的邮箱').optional().or(z.literal('')),
  phone: z.string().optional(),
  nickname: z.string().optional(),
}))

const editSchema = toTypedSchema(z.object({
  email: z.string().email('请输入有效的邮箱').optional().or(z.literal('')),
  phone: z.string().optional(),
  nickname: z.string().optional(),
}))

const { handleSubmit, setValues } = useForm({
  validationSchema: isEdit.value ? editSchema : createSchema,
})

const loading = ref(false)

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    if (isEdit.value) {
      const submitData: UserUpdate = values
      await userStore.editUser(userId.value, submitData)
    } else {
      const submitData: UserCreate = values as UserCreate
      await userStore.addUser(submitData)
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
    await userStore.fetchUser(userId.value)
    const user = userStore.currentUser
    if (user) {
      setValues({
        email: user.email || '',
        phone: user.phone || '',
        nickname: user.nickname || '',
      })
    }
  }
})
</script>

<template>
  <AppPage :title="isEdit ? '编辑用户' : '创建用户'" variant="detail">
    <form @submit="onSubmit" class="max-w-[600px] flex flex-col gap-6">
      <template v-if="!isEdit">
        <FormField v-slot="{ componentField }" name="username">
          <FormItem>
            <FormLabel>用户名</FormLabel>
            <FormControl>
              <Input v-bind="componentField" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField v-slot="{ componentField }" name="password">
          <FormItem>
            <FormLabel>密码</FormLabel>
            <FormControl>
              <Input v-bind="componentField" type="password" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>
      </template>

      <FormField v-slot="{ componentField }" name="nickname">
        <FormItem>
          <FormLabel>昵称</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="email">
        <FormItem>
          <FormLabel>邮箱</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="phone">
        <FormItem>
          <FormLabel>手机号</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <div class="flex gap-2">
        <Button type="submit" :disabled="loading">
          {{ isEdit ? '保存' : '创建' }}
        </Button>
        <Button variant="outline" @click="handleCancel">取消</Button>
      </div>
    </form>
  </AppPage>
</template>