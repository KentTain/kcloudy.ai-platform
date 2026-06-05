<script setup lang="ts">
/**
 * AdminConsoleLayout 管理后台布局
 * 参考 shadcn sidebar-08 设计
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AdminSidebar from '@/tenant/components/AdminSidebar.vue'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { Separator } from '@/components/ui/separator'
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'

const route = useRoute()

const breadcrumbItems = computed(() => {
  const items: { title: string; url?: string }[] = []
  const meta = route.meta

  if (meta?.title) {
    // 管理后台首页
    items.push({ title: '管理后台', url: '/admin' })

    // 当前页面
    if (route.path !== '/admin') {
      items.push({ title: meta.title as string })
    }
  }

  return items
})
</script>

<template>
  <SidebarProvider>
    <AdminSidebar />
    <SidebarInset>
      <header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger class="-ml-1" />
        <Separator orientation="vertical" class="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <template v-for="(item, index) in breadcrumbItems" :key="item.title">
              <BreadcrumbItem v-if="index < breadcrumbItems.length - 1">
                <BreadcrumbLink as-child>
                  <router-link :to="item.url || '#'">{{ item.title }}</router-link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator v-if="index < breadcrumbItems.length - 1" />
              <BreadcrumbItem v-if="index === breadcrumbItems.length - 1">
                <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
              </BreadcrumbItem>
            </template>
          </BreadcrumbList>
        </Breadcrumb>
      </header>
      <div class="flex flex-1 flex-col gap-4 p-4">
        <router-view />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
