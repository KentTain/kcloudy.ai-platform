<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { addDepartmentUser, removeDepartmentUser } from '@/iam/api/department'
import { useDepartmentStore } from '@/iam/stores/department'
import DepartmentTree from '@/iam/components/DepartmentTree.vue'
import type { CreateDepartmentParams, Department, UpdateDepartmentParams } from '@/iam/types'
import { confirmAction, getErrorMessage, notifyError, notifySuccess } from '@/iam/utils/feedback'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import DescriptionList from '@/components/DescriptionList.vue'
import type { DescriptionItem } from '@/components/DescriptionList.vue'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import Pagination from '@/components/Pagination.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import * as z from 'zod'
import { Plus, Pencil, Trash2, RefreshCw, UserPlus } from '@lucide/vue'

const departmentStore = useDepartmentStore()

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const currentDepartmentId = ref<string | null>(null)
const leaderId = ref('')
const savingLeader = ref(false)
const usersLoading = ref(false)
const addUserId = ref('')
const addUserAsLeader = ref(false)
const addingUser = ref(false)
const removingUserId = ref<string | null>(null)

const userPagination = ref({ page: 1, pageSize: 20 })

const formSchema = toTypedSchema(z.object({
  name: z.string().min(1, '请输入部门名称'),
  code: z.string().optional(),
  sort_order: z.number().optional(),
}))

const { handleSubmit: handleFormSubmit, setValues: setFormValues } = useForm({
  validationSchema: formSchema,
})

const flattenDepartments = (departments: Department[]): Department[] =>
  departments.flatMap(dept => [dept, ...flattenDepartments(dept.children || [])])

const selectedDepartment = computed(() => {
  if (!currentDepartmentId.value) return null
  return flattenDepartments(departmentStore.departmentTree).find(
    dept => dept.id === currentDepartmentId.value,
  ) || null
})

const departmentDescriptionItems = computed<DescriptionItem[]>(() => {
  const dept = selectedDepartment.value
  if (!dept) return []
  return [
    { label: '部门名称', value: dept.name },
    { label: '部门编码', value: dept.code },
    { label: '排序号', value: String(dept.sort_order) },
    { label: '负责人', value: dept.leader_id || '未设置' },
  ]
})

const loadDepartments = async () => {
  await departmentStore.fetchDepartmentTree()
}

const loadDepartmentUsers = async () => {
  if (!currentDepartmentId.value) return
  usersLoading.value = true
  try {
    await departmentStore.fetchUsers(currentDepartmentId.value)
  } finally {
    usersLoading.value = false
  }
}

const handleNodeClick = async (node: { id: string; data?: Department }) => {
  const dept = node.data
  if (!dept) return
  currentDepartmentId.value = node.id
  leaderId.value = dept.leader_id || ''
  addUserId.value = ''
  addUserAsLeader.value = false
  await loadDepartmentUsers()
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增部门'
  setFormValues({ name: '', code: '', sort_order: 0 })
  dialogVisible.value = true
}

const handleEdit = () => {
  if (!selectedDepartment.value) return
  const dept = selectedDepartment.value
  isEdit.value = true
  dialogTitle.value = '编辑部门'
  setFormValues({ name: dept.name, code: dept.code || '', sort_order: dept.sort_order })
  dialogVisible.value = true
}

const handleDelete = async () => {
  if (!currentDepartmentId.value) return
  if (!confirmAction('确定要删除该部门吗？')) return
  try {
    await departmentStore.removeDepartment(currentDepartmentId.value)
    currentDepartmentId.value = null
    leaderId.value = ''
    departmentStore.departmentUsers = []
    notifySuccess('删除成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '删除失败'))
  }
}

const onSubmitForm = handleFormSubmit(async (values) => {
  try {
    const formValues: CreateDepartmentParams & UpdateDepartmentParams = values
    if (isEdit.value && currentDepartmentId.value) {
      await departmentStore.editDepartment(currentDepartmentId.value, formValues)
      leaderId.value = formValues.leader_id || ''
      notifySuccess('更新成功')
    } else {
      await departmentStore.addDepartment(formValues)
      notifySuccess('创建成功')
    }
    dialogVisible.value = false
    await loadDepartments()
  } catch (error) {
    notifyError(getErrorMessage(error, '操作失败'))
  }
})

const handleSaveLeader = async () => {
  if (!currentDepartmentId.value) return
  savingLeader.value = true
  try {
    await departmentStore.updateLeader(currentDepartmentId.value, leaderId.value)
    await loadDepartments()
    notifySuccess('负责人保存成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '负责人保存失败'))
  } finally {
    savingLeader.value = false
  }
}

const handleAddDepartmentUser = async () => {
  if (!currentDepartmentId.value || !addUserId.value.trim()) return
  addingUser.value = true
  try {
    await addDepartmentUser(currentDepartmentId.value, addUserId.value.trim(), addUserAsLeader.value)
    addUserId.value = ''
    addUserAsLeader.value = false
    await Promise.all([loadDepartmentUsers(), loadDepartments()])
    notifySuccess('添加部门用户成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '添加部门用户失败'))
  } finally {
    addingUser.value = false
  }
}

const handleRemoveDepartmentUser = async (userId: string) => {
  if (!currentDepartmentId.value) return
  if (!confirmAction('确定要从该部门移除用户吗？')) return
  removingUserId.value = userId
  try {
    await removeDepartmentUser(currentDepartmentId.value, userId)
    await Promise.all([loadDepartmentUsers(), loadDepartments()])
    notifySuccess('移除部门用户成功')
  } catch (error) {
    notifyError(getErrorMessage(error, '移除部门用户失败'))
  } finally {
    removingUserId.value = null
  }
}

onMounted(() => {
  loadDepartments()
})
</script>

<template>
  <AppPage title="部门管理" variant="workbench">
    <template #actions>
      <Button @click="handleAdd">
        <Plus class="mr-1 h-4 w-4" />
        新增部门
      </Button>
    </template>

    <div class="grid grid-cols-12 gap-4">
      <!-- 左侧树 -->
      <div class="col-span-4">
        <div class="rounded-lg border p-3">
          <DepartmentTree
            :departments="departmentStore.departmentTree"
            :model-value="currentDepartmentId || ''"
            mode="single"
            :default-expand-level="99"
            @node-click="handleNodeClick"
          />
        </div>
      </div>

      <!-- 右侧详情 -->
      <div class="col-span-8">
        <div class="rounded-lg border p-4">
          <template v-if="selectedDepartment">
            <!-- 部门详情 -->
            <DescriptionList :items="departmentDescriptionItems" :columns="2" bordered />

            <div class="flex gap-2 mt-4">
              <Button size="sm" @click="handleEdit">
                <Pencil class="mr-1 h-3.5 w-3.5" />
                编辑
              </Button>
              <Button variant="destructive" size="sm" @click="handleDelete">
                <Trash2 class="mr-1 h-3.5 w-3.5" />
                删除
              </Button>
            </div>

            <div class="my-4 border-t" />

            <!-- 负责人设置 -->
            <div class="flex flex-col gap-2">
              <h3 class="text-sm font-medium">负责人设置</h3>
              <div class="flex items-center gap-2">
                <Input v-model="leaderId" placeholder="请输入负责人用户 ID" class="max-w-[360px]" />
                <Button size="sm" :disabled="savingLeader" @click="handleSaveLeader">保存负责人</Button>
              </div>
            </div>

            <div class="my-4 border-t" />

            <!-- 部门用户 -->
            <div class="flex flex-col gap-3">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-sm font-medium">部门用户</h3>
                  <p class="text-xs text-muted-foreground mt-1">展示当前部门用户，支持添加、移除和刷新用户列表。</p>
                </div>
                <Button variant="outline" size="sm" :disabled="usersLoading" @click="loadDepartmentUsers">
                  <RefreshCw class="mr-1 h-3.5 w-3.5" />
                  刷新
                </Button>
              </div>

              <div class="flex items-center gap-2">
                <Input v-model="addUserId" placeholder="请输入用户 ID" class="max-w-[320px]" />
                <div class="flex items-center gap-1.5">
                  <Checkbox v-model:checked="addUserAsLeader" />
                  <span class="text-sm">设为负责人</span>
                </div>
                <Button size="sm" :disabled="!addUserId.trim() || addingUser" @click="handleAddDepartmentUser">
                  <UserPlus class="mr-1 h-3.5 w-3.5" />
                  添加用户
                </Button>
              </div>

              <div class="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>用户名</TableHead>
                      <TableHead>昵称</TableHead>
                      <TableHead class="w-[100px]">负责人</TableHead>
                      <TableHead class="w-[120px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-if="usersLoading">
                      <TableCell v-for="n in 4" :key="n">
                        <Skeleton class="h-5 w-full" />
                      </TableCell>
                    </TableRow>
                    <TableRow v-else-if="!departmentStore.departmentUsers.length">
                      <TableCell colspan="4" class="h-16 text-center text-muted-foreground">暂无用户</TableCell>
                    </TableRow>
                    <TableRow v-else v-for="row in departmentStore.departmentUsers" :key="row.id">
                      <TableCell class="font-medium">{{ row.username }}</TableCell>
                      <TableCell>{{ row.nickname || '--' }}</TableCell>
                      <TableCell>
                        <Badge :variant="row.id === selectedDepartment?.leader_id ? 'default' : 'secondary'">
                          {{ row.id === selectedDepartment?.leader_id ? '是' : '否' }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          class="text-destructive hover:text-destructive"
                          :disabled="removingUserId === row.id"
                          @click="handleRemoveDepartmentUser(row.id)"
                        >
                          移除
                        </Button>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              <Pagination
                :total="departmentStore.departmentUsers.length"
                :page="userPagination.page"
                :page-size="userPagination.pageSize"
              />
            </div>
          </template>

          <div v-else class="py-8 text-center text-muted-foreground">
            请选择部门
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <Dialog v-model:open="dialogVisible">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{{ dialogTitle }}</DialogTitle>
          <DialogDescription>填写部门信息</DialogDescription>
        </DialogHeader>

        <form @submit="onSubmitForm" class="flex flex-col gap-4">
          <FormField v-slot="{ componentField }" name="name">
            <FormItem>
              <FormLabel>部门名称</FormLabel>
              <FormControl>
                <Input v-bind="componentField" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="code">
            <FormItem>
              <FormLabel>部门编码</FormLabel>
              <FormControl>
                <Input v-bind="componentField" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <DialogFooter>
            <Button variant="outline" @click="dialogVisible = false">取消</Button>
            <Button type="submit">确定</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>