<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getModule } from '@/tenant/api/module'
import type { Module } from '@/tenant/types/admin'
import { notifyError } from '@/framework/utils/feedback'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { ArrowLeft, Pencil, Package, Menu, Key, Users } from '@lucide/vue'

const route = useRoute()
const router = useRouter()

const moduleId = computed(() => route.params.id as string)
const moduleData = ref<Module | null>(null)
const loading = ref(false)

// 当前激活的 Tab
const activeTab = ref('info')

// 加载模块详情
const loadModule = async () => {
  loading.value = true
  try {
    const response = await getModule(moduleId.value)
    if (response.data) {
      moduleData.value = response.data
    }
  } catch (error) {
    console.error('加载模块详情失败:', error)
    notifyError('加载模块详情失败')
  } finally {
    loading.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.push('/admin/modules')
}

// 编辑模块
const handleEdit = () => {
  router.push(`/admin/modules/${moduleId.value}/edit`)
}

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString()
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
          <h2 class="text-xl font-semibold">
            <span v-if="loading"><Skeleton class="h-6 w-32" /></span>
            <span v-else>{{ moduleData?.name || '模块详情' }}</span>
          </h2>
          <p class="text-muted-foreground mt-1 text-sm">
            <span v-if="loading"><Skeleton class="h-4 w-24" /></span>
            <span v-else>{{ moduleData?.code || '--' }}</span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button @click="handleEdit">
          <Pencil class="mr-1 h-4 w-4" />
          编辑模块
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Package class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">模块状态</span>
        </div>
        <div class="mt-2">
          <Badge v-if="moduleData" :variant="moduleData.is_active ? 'default' : 'secondary'">
            {{ moduleData.is_active ? '启用' : '停用' }}
          </Badge>
          <Skeleton v-else class="h-5 w-12" />
        </div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Key class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">必须模块</span>
        </div>
        <div class="mt-2">
          <Badge v-if="moduleData" :variant="moduleData.is_need ? 'default' : 'outline'">
            {{ moduleData.is_need ? '是' : '否' }}
          </Badge>
          <Skeleton v-else class="h-5 w-12" />
        </div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Users class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">分配租户</span>
        </div>
        <div class="text-2xl font-semibold">
          <span v-if="moduleData">{{ moduleData.tenant_count || 0 }}</span>
          <Skeleton v-else class="h-7 w-8" />
        </div>
      </Card>
    </div>

    <!-- Tab 切换区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <Tabs v-model="activeTab" class="flex h-full flex-col">
        <div class="border-b px-5 pt-4">
          <TabsList>
            <TabsTrigger value="info">
              <Package class="mr-1 h-4 w-4" />
              基本信息
            </TabsTrigger>
            <TabsTrigger value="menus">
              <Menu class="mr-1 h-4 w-4" />
              菜单管理
            </TabsTrigger>
            <TabsTrigger value="permissions">
              <Key class="mr-1 h-4 w-4" />
              权限管理
            </TabsTrigger>
            <TabsTrigger value="roles">
              <Users class="mr-1 h-4 w-4" />
              角色管理
            </TabsTrigger>
          </TabsList>
        </div>

        <div class="min-h-0 flex-1 overflow-auto px-5 py-5">
          <!-- 基本信息 Tab -->
          <TabsContent value="info" class="mt-0">
            <div v-if="loading" class="space-y-4">
              <div v-for="n in 6" :key="n" class="grid gap-4 md:grid-cols-2">
                <Skeleton class="h-16 w-full" />
                <Skeleton class="h-16 w-full" />
              </div>
            </div>
            <div v-else-if="moduleData" class="grid gap-4 md:grid-cols-2">
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块名称</div>
                <div class="mt-2 font-medium">{{ moduleData.name }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块编码</div>
                <div class="mt-2 font-medium">{{ moduleData.code }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块图标</div>
                <div class="mt-2 font-medium">{{ moduleData.icon || '未设置' }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块状态</div>
                <div class="mt-2">
                  <Badge :variant="moduleData.is_active ? 'default' : 'secondary'">
                    {{ moduleData.is_active ? '启用' : '停用' }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">是否必须模块</div>
                <div class="mt-2">
                  <Badge :variant="moduleData.is_need ? 'default' : 'outline'">
                    {{ moduleData.is_need ? '是' : '否' }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">创建时间</div>
                <div class="mt-2 font-medium">{{ formatDate(moduleData.created_at) }}</div>
              </div>
              <div class="rounded-lg border p-4 md:col-span-2">
                <div class="text-muted-foreground text-xs">模块描述</div>
                <div class="mt-2 text-sm leading-6">{{ moduleData.description || '暂无描述' }}</div>
              </div>
            </div>
          </TabsContent>

          <!-- 菜单管理 Tab -->
          <TabsContent value="menus" class="mt-0">
            <div class="flex h-full flex-col items-center justify-center gap-4 py-12">
              <Menu class="text-muted-foreground h-16 w-16" />
              <div class="text-center">
                <div class="font-medium">菜单管理功能开发中</div>
                <div class="text-muted-foreground mt-1 text-sm">菜单管理功能将在后续实现</div>
              </div>
            </div>
          </TabsContent>

          <!-- 权限管理 Tab -->
          <TabsContent value="permissions" class="mt-0">
            <div class="flex h-full flex-col items-center justify-center gap-4 py-12">
              <Key class="text-muted-foreground h-16 w-16" />
              <div class="text-center">
                <div class="font-medium">权限管理功能开发中</div>
                <div class="text-muted-foreground mt-1 text-sm">权限管理功能将在后续实现</div>
              </div>
            </div>
          </TabsContent>

          <!-- 角色管理 Tab -->
          <TabsContent value="roles" class="mt-0">
            <div class="flex h-full flex-col items-center justify-center gap-4 py-12">
              <Users class="text-muted-foreground h-16 w-16" />
              <div class="text-center">
                <div class="font-medium">角色管理功能开发中</div>
                <div class="text-muted-foreground mt-1 text-sm">角色管理功能将在后续实现</div>
              </div>
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </Card>
  </div>
</template>
