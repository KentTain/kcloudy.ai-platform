<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import * as z from 'zod'
import { useRoleStore } from '@/iam/stores/role'
import { usePermissionStore } from '@/iam/stores/permission'
import PermissionTree from '@/iam/components/PermissionTree.vue'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Input } from '@/components'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components'

const route = useRoute()
const router = useRouter()
const roleStore = useRoleStore()
const permissionStore = usePermissionStore()

const isEdit = computed(() => !!route.params.id)
const roleId = computed(() => route.params.id as string)

const formSchema = toTypedSchema(z.object({
  code: z.string().min(1, '请输入角色编码'),
  name: z.string().min(1, '请输入角色名称'),
  description: z.string().optional(),
}))

const { handleSubmit, setValues } = useForm({
  validationSchema: formSchema,
})

const selectedPermissions = ref<string[]>([])
const loading = ref(false)

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    if (isEdit.value) {
      await roleStore.editRole(roleId.value, values)
      await roleStore.updateRolePermissions(roleId.value, selectedPermissions.value)
    } else {
      const newRole = await roleStore.addRole(values)
      if (newRole) {
        await roleStore.updateRolePermissions(newRole.id, selectedPermissions.value)
      }
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
  await permissionStore.fetchAllPermissions()

  if (isEdit.value) {
    await roleStore.fetchRole(roleId.value)
    await roleStore.fetchRolePermissions(roleId.value)

    const role = roleStore.currentRole
    if (role) {
      setValues({
        code: role.code,
        name: role.name,
        description: role.description || '',
      })
    }
    selectedPermissions.value = roleStore.currentRolePermissions.map(p => p.id)
  }
})
</script>

<template>
  <AppPage :title="isEdit ? '编辑角色' : '创建角色'" variant="detail">
    <form @submit="onSubmit" class="max-w-[800px] flex flex-col gap-6">
      <FormField v-slot="{ componentField }" name="code">
        <FormItem>
          <FormLabel>角色编码</FormLabel>
          <FormControl>
            <Input v-bind="componentField" :disabled="isEdit" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel>角色名称</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="description">
        <FormItem>
          <FormLabel>描述</FormLabel>
          <FormControl>
            <Input v-bind="componentField" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <div class="flex flex-col gap-2">
        <FormLabel>权限分配</FormLabel>
        <div class="rounded-lg border p-3 max-h-[400px] overflow-auto">
          <PermissionTree
            v-model="selectedPermissions"
            :permissions="permissionStore.permissions"
          />
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