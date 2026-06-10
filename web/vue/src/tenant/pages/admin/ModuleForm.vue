<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getModule, createModule, updateModule } from '@/tenant/api/module'
import type { CreateModuleParams, UpdateModuleParams } from '@/tenant/types/admin'
import { notifySuccess, notifyError } from '@/framework/utils/feedback'
import { Button, Input, Label, Card, Switch } from '@/components'
import { ArrowLeft, Save } from '@lucide/vue'

const route = useRoute()
const router = useRouter()

const moduleId = computed(() => route.params.id as string)
const isEdit = computed(() => !!moduleId.value)
const loading = ref(false)
const saving = ref(false)

// 表单数据
const form = ref({
  name: '',
  code: '',
  description: '',
  icon: '',
  is_active: true,
  is_need: false,
})

// 表单验证错误
const errors = ref<Record<string, string>>({})

// 加载模块详情（编辑模式）
const loadModule = async () => {
  if (!isEdit.value) return

  loading.value = true
  try {
    const response = await getModule(moduleId.value)
    if (response.data) {
      const data = response.data
      form.value = {
        name: data.name,
        code: data.code,
        description: data.description || '',
        icon: data.icon || '',
        is_active: data.is_active,
        is_need: data.is_need,
      }
    }
  } catch (error) {
    console.error('加载模块详情失败:', error)
    notifyError('加载模块详情失败')
  } finally {
    loading.value = false
  }
}

// 验证表单
const validateForm = (): boolean => {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = '请输入模块名称'
  }

  if (!form.value.code.trim()) {
    errors.value.code = '请输入模块编码'
  } else if (!/^[a-z][a-z0-9_]*$/.test(form.value.code)) {
    errors.value.code = '模块编码必须以小写字母开头，只能包含小写字母、数字和下划线'
  }

  return Object.keys(errors.value).length === 0
}

// 保存模块
const handleSave = async () => {
  if (!validateForm()) return

  saving.value = true
  try {
    if (isEdit.value) {
      const payload: UpdateModuleParams = {
        name: form.value.name,
        description: form.value.description || undefined,
        icon: form.value.icon || undefined,
        is_active: form.value.is_active,
      }
      await updateModule(moduleId.value, payload)
      notifySuccess('模块已更新')
    } else {
      const payload: CreateModuleParams = {
        name: form.value.name,
        code: form.value.code,
        description: form.value.description || undefined,
        icon: form.value.icon || undefined,
        is_active: form.value.is_active,
        is_need: form.value.is_need,
      }
      await createModule(payload)
      notifySuccess('模块已创建')
    }
    router.push('/admin/modules')
  } catch (error: any) {
    console.error('保存模块失败:', error)
    const errorMessage = error?.response?.data?.message || error?.message || '保存失败'
    notifyError(errorMessage)
  } finally {
    saving.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.push('/admin/modules')
}

onMounted(() => {
  loadModule()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" @click="handleBack">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold">{{ isEdit ? '编辑模块' : '新增模块' }}</h2>
          <p class="text-muted-foreground mt-1 text-sm">
            {{ isEdit ? '修改模块基本信息' : '创建新的系统模块' }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="handleBack">取消</Button>
        <Button :disabled="saving" @click="handleSave">
          <Save class="mr-1 h-4 w-4" />
          {{ saving ? '保存中...' : '保存' }}
        </Button>
      </div>
    </div>

    <!-- 表单区域 -->
    <Card class="flex min-h-0 flex-1 flex-col overflow-hidden p-6">
      <div v-if="loading" class="flex flex-col gap-4">
        <div v-for="n in 6" :key="n" class="space-y-2">
          <div class="h-4 w-20 bg-muted animate-pulse rounded" />
          <div class="h-10 w-full bg-muted animate-pulse rounded" />
        </div>
      </div>

      <div v-else class="mx-auto w-full max-w-2xl space-y-6">
        <!-- 模块名称 -->
        <div class="space-y-2">
          <Label for="name">模块名称 <span class="text-destructive">*</span></Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="请输入模块名称"
            :class="{ 'border-destructive': errors.name }"
          />
          <p v-if="errors.name" class="text-destructive text-xs">{{ errors.name }}</p>
        </div>

        <!-- 模块编码 -->
        <div class="space-y-2">
          <Label for="code">模块编码 <span class="text-destructive">*</span></Label>
          <Input
            id="code"
            v-model="form.code"
            placeholder="例如: user_management"
            :disabled="isEdit"
            :class="{ 'border-destructive': errors.code }"
          />
          <p v-if="errors.code" class="text-destructive text-xs">{{ errors.code }}</p>
          <p v-else class="text-muted-foreground text-xs">
            模块编码只能包含小写字母、数字和下划线，创建后不可修改
          </p>
        </div>

        <!-- 模块描述 -->
        <div class="space-y-2">
          <Label for="description">模块描述</Label>
          <textarea
            id="description"
            v-model="form.description"
            class="border-input placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[80px] w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请输入模块描述"
            rows="4"
          />
        </div>

        <!-- 模块图标 -->
        <div class="space-y-2">
          <Label for="icon">模块图标</Label>
          <Input
            id="icon"
            v-model="form.icon"
            placeholder="例如: Package"
          />
          <p class="text-muted-foreground text-xs">
            图标名称，使用 Lucide Icons 图标库
          </p>
        </div>

        <!-- 开关选项 -->
        <div class="grid gap-6 md:grid-cols-2">
          <!-- 是否启用 -->
          <div class="flex items-center justify-between rounded-lg border p-4">
            <div class="space-y-0.5">
              <Label for="is_active">是否启用</Label>
              <p class="text-muted-foreground text-xs">启用后模块可分配给租户使用</p>
            </div>
            <Switch
              id="is_active"
              v-model:checked="form.is_active"
            />
          </div>

          <!-- 是否必须模块 -->
          <div class="flex items-center justify-between rounded-lg border p-4">
            <div class="space-y-0.5">
              <Label for="is_need">是否必须模块</Label>
              <p class="text-muted-foreground text-xs">必须模块会自动分配给所有租户</p>
            </div>
            <Switch
              id="is_need"
              v-model:checked="form.is_need"
              :disabled="isEdit"
            />
          </div>
        </div>

        <p v-if="isEdit" class="text-muted-foreground text-xs">
          注意：是否必须模块创建后不可修改
        </p>
      </div>
    </Card>
  </div>
</template>
