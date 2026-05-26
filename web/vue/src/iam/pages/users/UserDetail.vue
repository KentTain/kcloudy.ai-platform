<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDepartments } from '@/iam/api/department'
import { getRoles } from '@/iam/api/role'
import {
  assignUserDepartments,
  assignUserRoles,
  getUserDepartments,
  getUserRoles,
  resetUserPassword,
} from '@/iam/api/user'
import { useUserStore } from '@/iam/stores/user'
import type { Department, Role } from '@/iam/types'
import { getErrorMessage, notifyError, notifySuccess } from '@/framework/utils/feedback'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import CommonDescriptionList from '@/components/CommonDescriptionList.vue'
import type { DescriptionItem } from '@/components/CommonDescriptionList.vue'
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
const departments = ref<Department[]>([])
const allRoles = ref<Role[]>([])
const allDepartments = ref<Department[]>([])
const selectedRoleIds = ref<string[]>([])
const selectedDepartmentIds = ref<string[]>([])
const loading = ref(false)
const savingRoles = ref(false)
const savingDepartments = ref(false)
const resettingPassword = ref(false)

const loadUserDetail = async () => {
  loading.value = true
  try {
    await userStore.fetchUser(userId.value)
    const [rolesRes, deptsRes, allRolesRes, allDepartmentsRes] = await Promise.all([
      getUserRoles(userId.value),
      getUserDepartments(userId.value),
      getRoles({ page: 1, page_size: 100 }),
      getDepartments(),
    ])
    roles.value = rolesRes.data
    departments.value = deptsRes.data
    selectedRoleIds.value = rolesRes.data.map(role => role.id)
    allRoles.value = allRolesRes.data.items
    allDepartments.value = allDepartmentsRes.data
    selectedDepartmentIds.value = deptsRes.data.map(dept => dept.id)
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
    notifySuccess(`密码重置成功，新密码：${response.data.password}`)
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
    roles.value = rolesRes.data
    selectedRoleIds.value = rolesRes.data.map(role => role.id)
    notifySuccess('角色分配保存成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '角色分配保存失败'))
  } finally {
    savingRoles.value = false
  }
}

const handleSaveDepartments = async () => {
  savingDepartments.value = true
  try {
    await assignUserDepartments(userId.value, selectedDepartmentIds.value)
    const deptsRes = await getUserDepartments(userId.value)
    departments.value = deptsRes.data
    selectedDepartmentIds.value = deptsRes.data.map(dept => dept.id)
    notifySuccess('部门分配保存成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '部门分配保存失败'))
  } finally {
    savingDepartments.value = false
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
    <CommonDescriptionList v-else :items="userDescriptionItems" :columns="2" bordered />

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

    <!-- 当前部门 -->
    <div v-if="!loading" class="flex flex-col gap-2">
      <h3 class="text-sm font-medium">当前部门</h3>
      <div class="flex flex-wrap gap-2">
        <Badge v-for="dept in departments" :key="dept.id" variant="outline">
          {{ dept.name }}
        </Badge>
        <span v-if="departments.length === 0" class="text-sm text-muted-foreground">暂无</span>
      </div>
    </div>

    <!-- 部门分配 -->
    <div v-if="!loading" class="flex flex-col gap-2">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-medium">部门分配</h3>
        <Button size="sm" :disabled="savingDepartments" @click="handleSaveDepartments">保存部门</Button>
      </div>
      <Select v-model="selectedDepartmentIds" multiple>
        <SelectTrigger class="w-full">
          <SelectValue placeholder="请选择部门" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="dept in allDepartments" :key="dept.id" :value="dept.id">
            {{ dept.name }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  </AppPage>
</template>