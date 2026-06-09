<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { changePassword, getLoginHistory, updateCurrentUser } from '@/iam/api/auth'
import { useTenantStore } from '@/tenant/stores/tenant'
import { getErrorMessage, notifyError, notifySuccess } from '@/framework/utils/feedback'
import { useUserStore } from '@/framework/stores'
import type { LoginHistory } from '@/iam/types'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { DateInput, DescriptionList, type DescriptionItem, Pagination } from '@/components/common'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import * as z from 'zod'
import { Save, KeyRound, ArrowRightLeft } from '@lucide/vue'

const frameworkUserStore = useUserStore()
const tenantStore = useTenantStore()

const activeTab = ref('profile')

// 个人资料
const profileSchema = toTypedSchema(z.object({
  nickname: z.string().optional(),
  email: z.string().email('请输入有效的邮箱').optional().or(z.literal('')),
  phone: z.string().optional(),
}))

const { handleSubmit: handleProfileSubmit } = useForm({
  validationSchema: profileSchema,
  initialValues: {
    nickname: frameworkUserStore.userInfo?.nickname || '',
    email: frameworkUserStore.userInfo?.email || '',
    phone: '',
  },
})

const profileLoading = ref(false)

const onProfileSubmit = handleProfileSubmit(async (values) => {
  profileLoading.value = true
  try {
    const response = await updateCurrentUser(values)
    const currentUserInfo = frameworkUserStore.userInfo
    if (currentUserInfo) {
      frameworkUserStore.setUserInfo({
        ...currentUserInfo,
        username: response.data.username,
        nickname: response.data.nickname || currentUserInfo.nickname,
        avatar: response.data.avatar,
        email: response.data.email,
        roles: currentUserInfo.roles,
        permissions: currentUserInfo.permissions,
      })
    }
    notifySuccess('资料更新成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '资料更新失败'))
  } finally {
    profileLoading.value = false
  }
})

// 修改密码
const passwordSchema = toTypedSchema(z.object({
  old_password: z.string().min(1, '请输入原密码'),
  new_password: z.string().min(8, '密码长度为 8-32 个字符').max(32, '密码长度为 8-32 个字符'),
  confirm_password: z.string().min(1, '请输入确认密码'),
}).refine(data => data.new_password === data.confirm_password, {
  message: '两次输入的密码不一致',
  path: ['confirm_password'],
}))

const { handleSubmit: handlePasswordSubmit } = useForm({
  validationSchema: passwordSchema,
})

const loading = ref(false)

const onPasswordSubmit = handlePasswordSubmit(async (values) => {
  loading.value = true
  try {
    await changePassword(values.old_password, values.new_password)
    notifySuccess('密码修改成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '密码修改失败'))
  } finally {
    loading.value = false
  }
})

// 租户切换
const handleSwitchTenant = async (tenantId: string) => {
  try {
    await tenantStore.switchTenant(tenantId)
    notifySuccess('租户切换成功')
    window.location.reload()
  } catch (error) {
    notifyError(getErrorMessage(error, '租户切换失败'))
  }
}

// 登录历史
const loginHistory = ref<LoginHistory[]>([])
const loginHistoryLoading = ref(false)
const loginHistoryTotal = ref(0)
const loginHistoryPage = ref(1)
const loginHistoryPageSize = ref(20)
const dateRange = ref<string | [string, string] | undefined>(undefined)

const loadLoginHistory = async () => {
  loginHistoryLoading.value = true
  try {
    const params: Record<string, unknown> = {
      page: loginHistoryPage.value,
      page_size: loginHistoryPageSize.value,
    }
    if (dateRange.value && Array.isArray(dateRange.value) && dateRange.value[0] && dateRange.value[1]) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const response = await getLoginHistory(params)
    loginHistory.value = response.data.items
    loginHistoryTotal.value = response.data.total
  } catch (error) {
    notifyError(getErrorMessage(error, '获取登录历史失败'))
  } finally {
    loginHistoryLoading.value = false
  }
}

watch(loginHistoryPage, () => loadLoginHistory())
watch(dateRange, () => {
  loginHistoryPage.value = 1
  loadLoginHistory()
})

watch(activeTab, (newTab) => {
  if (newTab === 'login-history') {
    loadLoginHistory()
  }
})

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatDeviceType = (type?: string) => {
  const typeMap: Record<string, string> = { desktop: '桌面端', mobile: '移动端', tablet: '平板' }
  return type ? typeMap[type] || type : '--'
}

const formatLoginStatus = (status: string) => status === 'success' ? '成功' : '失败'

// 个人信息描述列表
const profileDescriptionItems = computed<DescriptionItem[]>(() => {
  const user = frameworkUserStore.userInfo
  if (!user) return []
  return [
    { label: '用户名', value: user.username },
    { label: '昵称', value: user.nickname },
    { label: '邮箱', value: user.email },
    { label: '当前租户', value: tenantStore.currentTenant?.name || '默认租户' },
  ]
})

onMounted(async () => {
  await tenantStore.fetchMyTenants()
})
</script>

<template>
  <AppPage title="个人中心" variant="list">
    <Tabs v-model="activeTab" class="w-full">
      <TabsList>
        <TabsTrigger value="profile">个人资料</TabsTrigger>
        <TabsTrigger value="password">修改密码</TabsTrigger>
        <TabsTrigger value="tenant">切换租户</TabsTrigger>
        <TabsTrigger value="login-history">登录历史</TabsTrigger>
      </TabsList>

      <!-- 个人资料 Tab -->
      <TabsContent value="profile">
        <div class="flex flex-col gap-6 max-w-[600px]">
          <DescriptionList :items="profileDescriptionItems" :columns="2" bordered />

          <form @submit="onProfileSubmit" class="flex flex-col gap-4">
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

            <Button type="submit" :disabled="profileLoading">
              <Save class="mr-1 h-4 w-4" />
              保存
            </Button>
          </form>
        </div>
      </TabsContent>

      <!-- 修改密码 Tab -->
      <TabsContent value="password">
        <form @submit="onPasswordSubmit" class="max-w-[500px] flex flex-col gap-4">
          <FormField v-slot="{ componentField }" name="old_password">
            <FormItem>
              <FormLabel>原密码</FormLabel>
              <FormControl>
                <Input v-bind="componentField" type="password" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="new_password">
            <FormItem>
              <FormLabel>新密码</FormLabel>
              <FormControl>
                <Input v-bind="componentField" type="password" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="confirm_password">
            <FormItem>
              <FormLabel>确认密码</FormLabel>
              <FormControl>
                <Input v-bind="componentField" type="password" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <Button type="submit" :disabled="loading">
            <KeyRound class="mr-1 h-4 w-4" />
            修改密码
          </Button>
        </form>
      </TabsContent>

      <!-- 切换租户 Tab -->
      <TabsContent value="tenant">
        <div class="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>租户名称</TableHead>
                <TableHead>租户编码</TableHead>
                <TableHead>我的角色</TableHead>
                <TableHead class="w-[100px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="tenantStore.loading">
                <TableCell v-for="n in 4" :key="n">
                  <Skeleton class="h-5 w-full" />
                </TableCell>
              </TableRow>
              <TableRow v-else-if="!tenantStore.myTenants.length">
                <TableCell colspan="4" class="h-24 text-center text-muted-foreground">暂无租户</TableCell>
              </TableRow>
              <TableRow v-else v-for="tenant in tenantStore.myTenants" :key="tenant.tenant_id">
                <TableCell>{{ tenant.tenant_name }}</TableCell>
                <TableCell>{{ tenant.tenant_code }}</TableCell>
                <TableCell>
                  <div class="flex flex-wrap gap-1">
                    <Badge v-for="role in tenant.role_names" :key="role" variant="secondary">{{ role }}</Badge>
                    <Badge v-if="!tenant.role_names?.length" variant="outline">成员</Badge>
                  </div>
                </TableCell>
                <TableCell>
                  <Button size="sm" :disabled="tenant.is_current" @click="handleSwitchTenant(tenant.tenant_id)">
                    <ArrowRightLeft class="mr-1 h-3.5 w-3.5" />
                    切换
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </TabsContent>

      <!-- 登录历史 Tab -->
      <TabsContent value="login-history">
        <div class="flex flex-col gap-4">
          <div class="flex items-end gap-3">
            <div class="flex flex-col gap-1.5">
              <span class="text-sm text-muted-foreground">日期范围</span>
              <DateInput
                v-model="dateRange"
                type="range"
                placeholder="选择日期范围"
                class="w-[280px]"
              />
            </div>
          </div>

          <div class="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-[180px]">登录时间</TableHead>
                  <TableHead class="w-[140px]">IP 地址</TableHead>
                  <TableHead class="w-[100px]">设备类型</TableHead>
                  <TableHead class="w-[120px]">浏览器</TableHead>
                  <TableHead class="w-[120px]">操作系统</TableHead>
                  <TableHead class="w-[80px]">状态</TableHead>
                  <TableHead>位置</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loginHistoryLoading">
                  <TableCell v-for="n in 7" :key="n">
                    <Skeleton class="h-5 w-full" />
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="!loginHistory.length">
                  <TableCell colspan="7" class="h-24 text-center text-muted-foreground">暂无数据</TableCell>
                </TableRow>
                <TableRow v-else v-for="row in loginHistory" :key="row.id">
                  <TableCell>{{ formatDateTime(row.login_at) }}</TableCell>
                  <TableCell>{{ row.ip_address }}</TableCell>
                  <TableCell>{{ formatDeviceType(row.device_type) }}</TableCell>
                  <TableCell>{{ row.browser || '--' }}</TableCell>
                  <TableCell>{{ row.os || '--' }}</TableCell>
                  <TableCell>
                    <Badge :variant="row.status === 'success' ? 'default' : 'destructive'" size="sm">
                      {{ formatLoginStatus(row.status) }}
                    </Badge>
                  </TableCell>
                  <TableCell>{{ row.location || '--' }}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <Pagination
            :total="loginHistoryTotal"
            :page="loginHistoryPage"
            :page-size="loginHistoryPageSize"
            @update:page="(p: number) => loginHistoryPage = p"
            @update:page-size="(s: number) => { loginHistoryPageSize = s; loginHistoryPage = 1 }"
          />
        </div>
      </TabsContent>
    </Tabs>
  </AppPage>
</template>