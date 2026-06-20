<script setup lang="ts">
/**
 * UserFormDialog — 用户创建/编辑弹窗
 *
 * 支持创建新用户和编辑现有用户。
 * 包含：基本信息（用户名、昵称、邮箱、手机号）、所属部门（TreeSelect）、角色分配（Checkbox 列表）。
 */

import { ref, computed, watch, onMounted } from "vue"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
  TreeSelect,
  Checkbox,
  Badge,
} from "@/components"
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components"
import { ScrollArea } from "@/components/ui/scroll-area"
import { toTypedSchema } from "@vee-validate/zod"
import { useForm } from "vee-validate"
import * as z from "zod"
import type { User, Organization, RoleOption } from "@/iam/types"
import type { TreeSelectNode } from "@/framework/types/tree"
import { getOrganizationTree } from "@/iam/api/organization"
import { getRoleOptions } from "@/iam/api/user"

interface Props {
  open: boolean
  mode: "create" | "edit"
  user?: User | null
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  mode: "create",
  user: null,
})

const emit = defineEmits<{
  "update:open": [value: boolean]
  submit: [data: UserSubmitData]
}>()

export interface UserSubmitData {
  username: string
  password?: string
  nickname?: string
  email?: string
  phone?: string
  organization_id?: string
  role_ids: string[]
}

// 表单验证 schema
const createSchema = toTypedSchema(
  z.object({
    username: z
      .string()
      .min(3, "用户名长度为 3-50 个字符")
      .max(50, "用户名长度为 3-50 个字符"),
    password: z
      .string()
      .min(8, "密码长度为 8-32 个字符")
      .max(32, "密码长度为 8-32 个字符"),
    nickname: z.string().max(100, "昵称不能超过 100 个字符").optional().or(z.literal("")),
    email: z.string().email("请输入有效的邮箱").optional().or(z.literal("")),
    phone: z.string().max(20, "手机号格式不正确").optional().or(z.literal("")),
    organization_id: z.string().optional().or(z.literal("")),
  })
)

const editSchema = toTypedSchema(
  z.object({
    nickname: z.string().max(100, "昵称不能超过 100 个字符").optional().or(z.literal("")),
    email: z.string().email("请输入有效的邮箱").optional().or(z.literal("")),
    phone: z.string().max(20, "手机号格式不正确").optional().or(z.literal("")),
    organization_id: z.string().optional().or(z.literal("")),
  })
)

const { handleSubmit, setValues, resetForm } = useForm({
  validationSchema: props.mode === "edit" ? editSchema : createSchema,
})

const saving = ref(false)
const organizationTree = ref<Organization[]>([])
const roleOptions = ref<RoleOption[]>([])
const selectedRoleIds = ref<string[]>([])

// 弹窗标题
const dialogTitle = computed(() => (props.mode === "edit" ? "编辑用户" : "创建用户"))

// 将 Organization 转换为 TreeSelectNode
function toTreeSelectNodes(organizations: Organization[]): TreeSelectNode[] {
  return organizations.map((org) => ({
    id: org.id,
    name: org.name,
    children: org.children ? toTreeSelectNodes(org.children) : undefined,
    isLeaf: !org.children || org.children.length === 0,
  }))
}

const treeSelectData = computed(() => toTreeSelectNodes(organizationTree.value))

// 加载组织树和角色选项
async function loadOptions() {
  try {
    const [orgRes, roleRes] = await Promise.all([getOrganizationTree(), getRoleOptions()])
    organizationTree.value = orgRes.data || []
    roleOptions.value = roleRes.data || []
  } catch (error) {
    console.error("加载选项失败:", error)
  }
}

// 切换角色选中
function toggleRole(roleId: string) {
  const index = selectedRoleIds.value.indexOf(roleId)
  if (index > -1) {
    selectedRoleIds.value.splice(index, 1)
  } else {
    selectedRoleIds.value.push(roleId)
  }
}

// 初始化表单
function initForm() {
  resetForm()
  selectedRoleIds.value = []

  if (props.mode === "edit" && props.user) {
    setValues({
      nickname: props.user.nickname || "",
      email: props.user.email || "",
      phone: props.user.phone || "",
      organization_id: props.user.organization_id || "",
    })
    selectedRoleIds.value = props.user.role_ids || []
  } else {
    setValues({
      username: "",
      password: "",
      nickname: "",
      email: "",
      phone: "",
      organization_id: "",
    })
  }
}

watch(
  () => props.open,
  (val) => {
    if (val) initForm()
  }
)

onMounted(() => {
  loadOptions()
})

const onSubmit = handleSubmit(async (values) => {
  saving.value = true
  try {
    const data: UserSubmitData = {
      username: props.mode === "edit" ? props.user!.username : (values as any).username,
      password: props.mode === "create" ? (values as any).password : undefined,
      nickname: values.nickname || undefined,
      email: values.email || undefined,
      phone: values.phone || undefined,
      organization_id: values.organization_id || undefined,
      role_ids: selectedRoleIds.value,
    }
    emit("submit", data)
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[520px]">
      <DialogHeader>
        <DialogTitle>{{ dialogTitle }}</DialogTitle>
        <DialogDescription>
          {{ mode === "edit" ? "修改用户信息" : "填写用户信息以创建新用户" }}
        </DialogDescription>
      </DialogHeader>

      <form @submit="onSubmit" class="flex flex-col gap-4">
        <!-- 用户名（创建时显示） -->
        <FormField v-if="mode === 'create'" v-slot="{ componentField }" name="username">
          <FormItem>
            <FormLabel>用户名 *</FormLabel>
            <FormControl>
              <Input v-bind="componentField" placeholder="请输入用户名" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 密码（创建时显示） -->
        <FormField v-if="mode === 'create'" v-slot="{ componentField }" name="password">
          <FormItem>
            <FormLabel>密码 *</FormLabel>
            <FormControl>
              <Input v-bind="componentField" type="password" placeholder="请输入密码" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 昵称 -->
        <FormField v-slot="{ componentField }" name="nickname">
          <FormItem>
            <FormLabel>昵称</FormLabel>
            <FormControl>
              <Input v-bind="componentField" placeholder="请输入昵称" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 邮箱 -->
        <FormField v-slot="{ componentField }" name="email">
          <FormItem>
            <FormLabel>邮箱</FormLabel>
            <FormControl>
              <Input v-bind="componentField" type="email" placeholder="请输入邮箱" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 手机号 -->
        <FormField v-slot="{ componentField }" name="phone">
          <FormItem>
            <FormLabel>手机号</FormLabel>
            <FormControl>
              <Input v-bind="componentField" placeholder="请输入手机号" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 所属组织 -->
        <FormField v-slot="{ componentField }" name="organization_id">
          <FormItem>
            <FormLabel>所属组织</FormLabel>
            <FormControl>
              <TreeSelect
                v-bind="componentField"
                :data="treeSelectData"
                :searchable="true"
                placeholder="请选择所属组织"
                :clearable="true"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 角色分配 -->
        <div class="space-y-2">
          <FormLabel>角色分配</FormLabel>
          <ScrollArea class="h-[120px] border rounded-md p-2">
            <div v-if="roleOptions.length === 0" class="text-sm text-muted-foreground text-center py-4">
              暂无可分配的角色
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="role in roleOptions"
                :key="role.id"
                class="flex items-center gap-2 py-1 px-2 rounded hover:bg-accent cursor-pointer"
                @click="toggleRole(role.id)"
              >
                <Checkbox
                  :checked="selectedRoleIds.includes(role.id)"
                  @update:checked="toggleRole(role.id)"
                />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium truncate">{{ role.name }}</p>
                  <p v-if="role.description" class="text-xs text-muted-foreground truncate">
                    {{ role.description }}
                  </p>
                </div>
                <Badge v-if="selectedRoleIds.includes(role.id)" variant="secondary" class="shrink-0">
                  已选
                </Badge>
              </div>
            </div>
          </ScrollArea>
        </div>

        <DialogFooter>
          <Button variant="outline" type="button" @click="$emit('update:open', false)">
            取消
          </Button>
          <Button type="submit" :disabled="saving">
            {{ saving ? "保存中..." : "确定" }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
