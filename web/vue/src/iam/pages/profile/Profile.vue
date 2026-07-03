<script setup lang="ts">
/**
 * Profile — 账户管理页面
 *
 * 布局：
 * - 头部：头像区（圆形头像 + 用户名 + 描述）
 * - Tabs：个人信息、安全设置
 */

import { computed, h, onMounted, ref, watch } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import { changePassword, getLoginHistory, updateCurrentUser } from "@/iam/api/auth"
import { useTenantStore } from "@/tenant/stores/tenant"
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback"
import { useUserStore } from "@/framework/stores"
import type { LoginHistory } from "@/iam/types"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Input,
  Badge,
  DateInput,
  Card,
  DataTable,
  useDataTable,
} from "@/components"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components"
import { toTypedSchema } from "@vee-validate/zod"
import { useForm } from "vee-validate"
import * as z from "zod"
import { Save, KeyRound, User, Shield, Eye, EyeOff } from "@lucide/vue"

const frameworkUserStore = useUserStore()
const tenantStore = useTenantStore()

const activeTab = ref("profile")

// ========== 个人资料 ==========

const profileSchema = toTypedSchema(
  z.object({
    nickname: z.string().max(100, "昵称不能超过 100 个字符").optional().or(z.literal("")),
    email: z.string().email("请输入有效的邮箱").optional().or(z.literal("")),
    phone: z.string().max(20, "手机号格式不正确").optional().or(z.literal("")),
  })
)

const { handleSubmit: handleProfileSubmit, setValues } = useForm({
  validationSchema: profileSchema,
})

const profileLoading = ref(false)

const onProfileSubmit = handleProfileSubmit(async (values) => {
  profileLoading.value = true
  try {
    const response = await updateCurrentUser({
      nickname: values.nickname || undefined,
      email: values.email || undefined,
      phone: values.phone || undefined,
    })
    const currentUserInfo = frameworkUserStore.userInfo
    const data = response.data
    if (currentUserInfo && data) {
      frameworkUserStore.setUserInfo({
        ...currentUserInfo,
        username: data.username,
        nickname: data.nickname || currentUserInfo.nickname,
        avatar: data.avatar,
        email: data.email,
        roles: currentUserInfo.roles,
        permissions: currentUserInfo.permissions,
      })
    }
    notifySuccess("资料更新成功")
  } catch (error) {
    notifyError(getErrorMessage(error, "资料更新失败"))
  } finally {
    profileLoading.value = false
  }
})

// 初始化表单值
function initProfileForm() {
  const user = frameworkUserStore.userInfo
  if (user) {
    setValues({
      nickname: user.nickname || "",
      email: user.email || "",
      phone: user.phone || "",
    })
  }
}

watch(
  () => frameworkUserStore.userInfo,
  () => initProfileForm(),
  { immediate: true }
)

// ========== 修改密码弹窗 ==========

const passwordDialogOpen = ref(false)
const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const passwordSchema = toTypedSchema(
  z
    .object({
      old_password: z.string().min(1, "请输入原密码"),
      new_password: z
        .string()
        .min(8, "密码长度为 8-32 个字符")
        .max(32, "密码长度为 8-32 个字符"),
      confirm_password: z.string().min(1, "请输入确认密码"),
    })
    .refine((data) => data.new_password === data.confirm_password, {
      message: "两次输入的密码不一致",
      path: ["confirm_password"],
    })
)

const { handleSubmit: handlePasswordSubmit, resetForm: resetPasswordForm } = useForm({
  validationSchema: passwordSchema,
})

const passwordLoading = ref(false)

const onPasswordSubmit = handlePasswordSubmit(async (values) => {
  passwordLoading.value = true
  try {
    await changePassword(values.old_password, values.new_password)
    notifySuccess("密码修改成功")
    passwordDialogOpen.value = false
    resetPasswordForm()
  } catch (error) {
    notifyError(getErrorMessage(error, "密码修改失败"))
  } finally {
    passwordLoading.value = false
  }
})

// ========== 登录历史 ==========

const dateRange = ref<string | [string, string] | undefined>(undefined)

// 格式化函数
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return "--"
  return new Date(dateStr).toLocaleString("zh-CN")
}

const formatDeviceType = (type?: string) => {
  const typeMap: Record<string, string> = { desktop: "桌面端", mobile: "移动端", tablet: "平板" }
  return type ? typeMap[type] || type : "--"
}

const formatLoginStatus = (status: string) => (status === "success" ? "成功" : "失败")

// 列定义
const loginHistoryColumns: ColumnDef<LoginHistory>[] = [
  {
    accessorKey: "login_at",
    header: "登录时间",
    size: 160,
    cell: ({ row }) => formatDateTime(row.original.login_at),
  },
  {
    accessorKey: "ip_address",
    header: "IP 地址",
    size: 120,
    cell: ({ row }) => row.original.ip_address,
  },
  {
    accessorKey: "device_type",
    header: "设备",
    size: 80,
    cell: ({ row }) => formatDeviceType(row.original.device_type),
  },
  {
    accessorKey: "status",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const status = row.original.status
      return h(Badge, { variant: status === "success" ? "default" : "destructive", size: "sm" }, () =>
        formatLoginStatus(status)
      )
    },
  },
  {
    accessorKey: "location",
    header: "位置",
    cell: ({ row }) => row.original.location || "--",
  },
]

// DataTable 初始化
const loginHistoryTable = useDataTable<LoginHistory>({
  columns: loginHistoryColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const params: Record<string, unknown> = { page, page_size }
    if (dateRange.value && Array.isArray(dateRange.value) && dateRange.value[0] && dateRange.value[1]) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const response = await getLoginHistory(params)
    return response
  },
})

watch(dateRange, () => {
  loginHistoryTable.refresh(true)
})

watch(activeTab, (newTab) => {
  if (newTab === "security") {
    loginHistoryTable.refresh(true)
  }
})

// ========== 用户信息 ==========

const userInfo = computed(() => frameworkUserStore.userInfo)

onMounted(async () => {
  await tenantStore.fetchMyTenants()
})
</script>

<template>
  <AppPage title="账户管理" variant="list">
    <!-- 头像区 -->
    <div class="flex items-center gap-4 pb-4 border-b">
      <div class="flex items-center justify-center w-16 h-16 rounded-full bg-primary text-primary-foreground text-xl font-bold">
        {{ userInfo?.nickname?.charAt(0) || userInfo?.username?.charAt(0) || "U" }}
      </div>
      <div>
        <h2 class="text-xl font-semibold">{{ userInfo?.nickname || userInfo?.username || "用户" }}</h2>
        <p class="text-sm text-muted-foreground">{{ userInfo?.email || "管理您的账户信息和安全设置" }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs v-model="activeTab" class="mt-4">
      <TabsList>
        <TabsTrigger value="profile">
          <User class="h-4 w-4 mr-1" />
          个人信息
        </TabsTrigger>
        <TabsTrigger value="security">
          <Shield class="h-4 w-4 mr-1" />
          安全设置
        </TabsTrigger>
      </TabsList>

      <!-- 个人信息 Tab -->
      <TabsContent value="profile" class="mt-4">
        <Card class="p-6 max-w-[600px]">
          <form @submit="onProfileSubmit" class="flex flex-col gap-4">
            <FormField v-slot="{ componentField }" name="nickname">
              <FormItem>
                <FormLabel>昵称</FormLabel>
                <FormControl>
                  <Input v-bind="componentField" placeholder="请输入昵称" />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField v-slot="{ componentField }" name="email">
              <FormItem>
                <FormLabel>邮箱</FormLabel>
                <FormControl>
                  <Input v-bind="componentField" type="email" placeholder="请输入邮箱" />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField v-slot="{ componentField }" name="phone">
              <FormItem>
                <FormLabel>手机号</FormLabel>
                <FormControl>
                  <Input v-bind="componentField" placeholder="请输入手机号" />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <div class="flex justify-end pt-2">
              <Button type="submit" :disabled="profileLoading">
                <Save class="mr-1 h-4 w-4" />
                保存修改
              </Button>
            </div>
          </form>
        </Card>
      </TabsContent>

      <!-- 安全设置 Tab -->
      <TabsContent value="security" class="mt-4">
        <div class="max-w-[800px] space-y-4">
          <!-- 密码项 -->
          <Card class="p-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium">密码</h3>
                <p class="text-sm text-muted-foreground">定期更换密码可以提高账户安全性</p>
              </div>
              <Button variant="outline" @click="passwordDialogOpen = true">
                <KeyRound class="mr-1 h-4 w-4" />
                修改密码
              </Button>
            </div>
          </Card>

          <!-- 登录历史 -->
          <Card class="p-4">
            <div class="mb-4">
              <h3 class="font-medium">登录历史</h3>
              <p class="text-sm text-muted-foreground">查看最近的登录记录</p>
            </div>

            <div class="mb-3">
              <DateInput
                v-model="dateRange"
                type="range"
                placeholder="选择日期范围"
                class="w-[280px]"
              />
            </div>

            <DataTable :data-table="loginHistoryTable" :fixed-layout="true" />
          </Card>
        </div>
      </TabsContent>
    </Tabs>

    <!-- 修改密码弹窗 -->
    <Dialog v-model:open="passwordDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>修改密码</DialogTitle>
          <DialogDescription>请输入原密码和新密码</DialogDescription>
        </DialogHeader>

        <form @submit="onPasswordSubmit" class="flex flex-col gap-4">
          <FormField v-slot="{ componentField }" name="old_password">
            <FormItem>
              <FormLabel>原密码</FormLabel>
              <FormControl>
                <div class="relative">
                  <Input
                    v-bind="componentField"
                    :type="showOldPassword ? 'text' : 'password'"
                    placeholder="请输入原密码"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    class="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    @click="showOldPassword = !showOldPassword"
                  >
                    <Eye v-if="!showOldPassword" class="h-4 w-4 text-muted-foreground" />
                    <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                  </Button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="new_password">
            <FormItem>
              <FormLabel>新密码</FormLabel>
              <FormControl>
                <div class="relative">
                  <Input
                    v-bind="componentField"
                    :type="showNewPassword ? 'text' : 'password'"
                    placeholder="请输入新密码（8-32位）"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    class="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    @click="showNewPassword = !showNewPassword"
                  >
                    <Eye v-if="!showNewPassword" class="h-4 w-4 text-muted-foreground" />
                    <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                  </Button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="confirm_password">
            <FormItem>
              <FormLabel>确认密码</FormLabel>
              <FormControl>
                <div class="relative">
                  <Input
                    v-bind="componentField"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    placeholder="请再次输入新密码"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    class="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    <Eye v-if="!showConfirmPassword" class="h-4 w-4 text-muted-foreground" />
                    <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                  </Button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <DialogFooter>
            <Button variant="outline" type="button" @click="passwordDialogOpen = false">
              取消
            </Button>
            <Button type="submit" :disabled="passwordLoading">
              {{ passwordLoading ? "修改中..." : "确定" }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
