<script setup lang="ts">
/**
 * CreateOrganizationDialog — 组织创建/编辑弹窗
 *
 * 支持新增一级组织、新增子组织、新增同级组织、编辑组织。
 * 使用 vee-validate + zod 表单验证。
 */

import { ref, watch, computed, onMounted } from "vue"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
  Textarea,
  TreeSelect,
} from "@/components"
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components"
import { toTypedSchema } from "@vee-validate/zod"
import { useForm } from "vee-validate"
import * as z from "zod"
import type { Organization } from "@/iam/types"
import type { TreeSelectNode } from "@/framework/types/tree"

interface Props {
  open: boolean
  mode: "create-root" | "create-child" | "create-sibling" | "edit"
  parentOrganization?: Organization | null
  currentOrganization?: Organization | null
  /** 组织树数据（用于 TreeSelect 选择上级组织） */
  organizationTree?: Organization[]
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  mode: "create-root",
  parentOrganization: null,
  currentOrganization: null,
  organizationTree: () => [],
})

const emit = defineEmits<{
  "update:open": [value: boolean]
  submit: [data: SubmitData]
}>()

export interface SubmitData {
  name: string
  code?: string
  parent_id?: string
  sort_order?: number
  leader_id?: string
  description?: string
}

// 表单验证 schema
const formSchema = toTypedSchema(
  z.object({
    name: z.string().min(1, "请输入组织名称").max(100, "组织名称不能超过 100 个字符"),
    code: z.string().max(50, "组织编码不能超过 50 个字符").optional().or(z.literal("")),
    sort_order: z.coerce.number().int().min(0, "排序号不能为负数").optional().default(0),
    parent_id: z.string().optional().or(z.literal("")),
    leader_id: z.string().optional().or(z.literal("")),
    description: z.string().max(200, "描述不能超过 200 个字符").optional().or(z.literal("")),
  })
)

const { handleSubmit, setValues, resetForm } = useForm({
  validationSchema: formSchema,
})

const saving = ref(false)

// 弹窗标题
const dialogTitle = computed(() => {
  switch (props.mode) {
    case "create-root":
      return "新增一级组织"
    case "create-child":
      return "新增子组织"
    case "create-sibling":
      return "新增同级组织"
    case "edit":
      return "编辑组织"
    default:
      return "组织操作"
  }
})

// 将 Organization 转换为 TreeSelectNode
function toTreeSelectNodes(organizations: Organization[]): TreeSelectNode[] {
  return organizations.map((org) => ({
    id: org.id,
    name: org.name,
    children: org.children ? toTreeSelectNodes(org.children) : undefined,
    isLeaf: !org.children || org.children.length === 0,
  }))
}

const treeSelectData = computed(() => toTreeSelectNodes(props.organizationTree))

// 初始化表单数据
function initForm() {
  let parentId = ""
  let formName = ""
  let formCode = ""
  let formSortOrder = 0

  switch (props.mode) {
    case "create-root":
      break
    case "create-child":
      parentId = props.currentOrganization?.id || ""
      break
    case "create-sibling":
      parentId = props.currentOrganization?.parent_id || ""
      break
    case "edit":
      formName = props.currentOrganization?.name || ""
      formCode = props.currentOrganization?.code || ""
      formSortOrder = props.currentOrganization?.sort_order ?? 0
      parentId = props.currentOrganization?.parent_id || ""
      break
  }

  resetForm()
  setValues({
    name: formName,
    code: formCode,
    sort_order: formSortOrder,
    parent_id: parentId,
    leader_id: "",
    description: "",
  })
}

watch(
  () => props.open,
  (val) => {
    if (val) initForm()
  }
)

const onSubmit = handleSubmit(async (values) => {
  saving.value = true
  try {
    emit("submit", {
      name: values.name,
      code: values.code || undefined,
      parent_id: values.parent_id || undefined,
      sort_order: values.sort_order || 0,
      leader_id: values.leader_id || undefined,
      description: values.description || undefined,
    })
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[480px]">
      <DialogHeader>
        <DialogTitle>{{ dialogTitle }}</DialogTitle>
        <DialogDescription>
          <template v-if="mode === 'edit'">
            修改组织信息
          </template>
          <template v-else>
            填写组织信息以创建新的组织节点
          </template>
        </DialogDescription>
      </DialogHeader>

      <form @submit="onSubmit" class="flex flex-col gap-4">
        <!-- 上级组织 -->
        <FormField v-slot="{ componentField }" name="parent_id">
          <FormItem>
            <FormLabel>上级组织</FormLabel>
            <FormControl>
              <TreeSelect
                v-bind="componentField"
                :data="treeSelectData"
                :searchable="true"
                placeholder="请选择上级组织（留空为一级组织）"
                :clearable="true"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 组织名称 -->
        <FormField v-slot="{ componentField }" name="name">
          <FormItem>
            <FormLabel>组织名称 *</FormLabel>
            <FormControl>
              <Input v-bind="componentField" placeholder="请输入组织名称" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 组织编码 -->
        <FormField v-slot="{ componentField }" name="code">
          <FormItem>
            <FormLabel>组织编码</FormLabel>
            <FormControl>
              <Input v-bind="componentField" placeholder="请输入编码（可选）" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 排序号 -->
        <FormField v-slot="{ componentField }" name="sort_order">
          <FormItem>
            <FormLabel>排序号</FormLabel>
            <FormControl>
              <Input v-bind="componentField" type="number" placeholder="0" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- 描述 -->
        <FormField v-slot="{ componentField }" name="description">
          <FormItem>
            <FormLabel>描述</FormLabel>
            <FormControl>
              <Textarea v-bind="componentField" placeholder="请输入描述（可选）" class="h-20" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

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
