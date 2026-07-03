<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrganizations } from '@/iam/api/organization'
import { getRoles } from '@/iam/api/role'
import {
  assignUserOrganizations,
  assignUserRoles,
  getUserOrganizations,
  getUserRoles,
  resetUserPassword,
} from '@/iam/api/user'
import { useUserStore } from '@/iam/stores/user'
import type { Organization, Role } from '@/iam/types'
import { getErrorMessage, notifyError, notifySuccess } from '@/framework/utils/feedback'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Badge, DescriptionList, type DescriptionItem } from '@/components'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Pencil, KeyRound } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const userId = computed(() => route.params.id as string)
const roles = ref<Role[]>([])
const organizations = ref<Organization[]>([])
const allRoles = ref<Role[]>([])
const allOrganizations = ref<Organization[]>([])
const selectedRoleIds = ref<string[]>([])
const selectedOrganizationIds = ref<string[]>([])
const loading = ref(false)
const savingRoles = ref(false)
const savingOrganizations = ref(false)
const resettingPassword = ref(false)

const loadUserDetail = async () => {
  loading.value = true
  try {
    await userStore.fetchUser(userId.value)
    const [rolesRes, orgsRes, allRolesRes, allOrganizationsRes] = await Promise.all([
      getUserRoles(userId.value),
      getUserOrganizations(userId.value),
      getRoles({ page: 1, page_size: 100 }),
      getOrganizations(),
    ])
    roles.value = rolesRes.data ?? []
    organizations.value = orgsRes.data ?? []
    selectedRoleIds.value = (rolesRes.data ?? []).map(role => role.id)
    allRoles.value = allRolesRes.data ?? []
    allOrganizations.value = allOrganizationsRes.data ?? []
    selectedOrganizationIds.value = (orgsRes.data ?? []).map(org => org.id)
  } catch (error) {
    notifyError(getErrorMessage(error, '加载用户详情失败'))
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  router.push(`/users/${userId.value}/edit`)
}

const handleBack = () => {
  router.back()
}

const handleResetPassword = async () => {
  resettingPassword.value = true
  try {
    const response = await resetUserPassword(userId.value)
    const password = response.data?.password
    if (password) {
      notifySuccess(`密码重置成功，新密码：${password}`)
    } else {
      notifySuccess('密码重置成功')
    }
  } catch (error) {
    notifyError(getErrorMessage(error, '重置密码失败'))
  } finally {
    resettingPassword.value = false
  }
}

const handleSaveRoles = async () => {
  savingRoles.value = true
  try {
    await assignUserRoles(userId.value, selectedRoleIds.value)
    const rolesRes = await getUserRoles(userId.value)
    roles.value = rolesRes.data ?? []
    selectedRoleIds.value = (rolesRes.data ?? []).map(role => role.id)
    notifySuccess('角色分配保存成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '角色分配保存失败'))
  } finally {
    savingRoles.value = false
  }
}

const handleSaveOrganizations = async () => {
  savingOrganizations.value = true
  try {
    await assignUserOrganizations(userId.value, selectedOrganizationIds.value)
    const orgsRes = await getUserOrganizations(userId.value)
    organizations.value = orgsRes.data ?? []
    selectedOrganizationIds.value = (orgsRes.data ?? []).map(org => org.id)
    notifySuccess('组织分配保存成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '组织分配保存失败'))
  } finally {
    savingOrganizations.value = false
  }
}

const userDescriptionItems = computed<DescriptionItem[]>(() => {
  const user = userStore.currentUser
  if (!user) return []

  return [
    { label: '用户名', value: user.username },
    { label: '昵称', value: user.nickname },
    { label: '邮箱', value: user.email },
    { label: '手机号', value: user.phone },
    {
      label: '状态',
      value: user.status === 'active' ? '激活' : user.status === 'locked' ? '锁定' : '停用',
      type: 'badge',
      badgeVariant: user.status === 'active' ? 'default' : user.status === 'locked' ? 'destructive' : 'secondary',
    },
    { label: '创建时间', value: new Date(user.created_at).toLocaleString() },
  ]
})

onMounted(() => {
  loadUserDetail()
})
</script>

<template>
  <AppPage title="用户详情" variant="detail">
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="handleBack">返回</Button>
        <Button variant="outline" :disabled="resettingPassword" @click="handleResetPassword">
          <KeyRound class="mr-1 h-4 w-4" />
          重置密码
        </Button>
        <Button @click="handleEdit">
          <Pencil class="mr-1 h-4 w-4" />
          编辑
        </Button>
      </div>
    </template>

    <!-- 用户基本信息 -->
    <div v-if="loading" class="flex flex-col gap-3">
      <div v-for="n in 6" :key="n" class="h-5 w-full bg-muted animate-pulse rounded" />
    </div>
    <DescriptionList v-else :items="userDescriptionItems" :columns="2" bordered />

    <!-- 当前角色 -->
    <div v-if="!loading" class="flex flex-col gap-2">
      <h3 class="text-sm font-medium">当前角色</h3>
      <div class="flex flex-wrap gap-2">
        <Badge v-for="role in roles" :key="role.id" variant="secondary">
          {{ role.name }}
        </Badge>
        <span v-if="roles.length === 0" class="text-sm text-muted-foreground">暂无</span>
      </div>
    </div>

    <!-- 角色分配 -->
    <div v-if="!loading" class="flex flex-col gap-2">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-medium">角色分配</h3>
        <Button size="sm" :disabled="savingRoles" @click="handleSaveRoles">保存角色</Button>
      </div>
      <Select v-model="selectedRoleIds" multiple>
        <SelectTrigger class="w-full">
          <SelectValue placeholder="请选择角色" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="role in allRoles" :key="role.id" :value="role.id">
            {{ role.name }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- 当前组织 -->
    <div v-if="!loading" class="flex flex-col gap-2">
      <h3 class="text-sm font-medium">当前组织</h3>
      <div class="flex flex-wrap gap-2">
        <Badge v-for="org in organizations" :key="org.id" variant="outline">
          {{ org.name }}
        </Badge>
        <span v-if="organizations.length === 0" class="text-sm text-muted-foreground">暂无</span>
      </div>
    </div>

    <!-- 组织分配 -->
    <div v-if="!loading" class="flex flex-col gap-2">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-medium">组织分配</h3>
        <Button size="sm" :disabled="savingOrganizations" @click="handleSaveOrganizations">保存组织</Button>
      </div>
      <Select v-model="selectedOrganizationIds" multiple>
        <SelectTrigger class="w-full">
          <SelectValue placeholder="请选择组织" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="org in allOrganizations" :key="org.id" :value="org.id">
            {{ org.name }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  </AppPage>
</template>