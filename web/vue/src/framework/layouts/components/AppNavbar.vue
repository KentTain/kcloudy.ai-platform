<script setup lang="ts">
/**
 * AppNavbar 顶部导航组件
 */
import { computed } from "vue";
import { useRoute } from "vue-router";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

const route = useRoute();

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title);
  return matched.map((item) => ({
    title: item.meta?.title as string,
    path: item.path,
  }));
});
</script>

<template>
  <header class="flex h-14 items-center gap-2 border-b bg-background px-4">
    <SidebarTrigger />
    <Separator orientation="vertical" class="h-6 mr-2" />
    <Breadcrumb v-if="breadcrumbs.length > 0">
      <BreadcrumbList>
        <template v-for="(item, index) in breadcrumbs" :key="item.path">
          <BreadcrumbItem v-if="index < breadcrumbs.length - 1">
            <BreadcrumbLink :href="item.path">
              {{ item.title }}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator v-if="index < breadcrumbs.length - 1" />
          <BreadcrumbItem v-if="index === breadcrumbs.length - 1">
            <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
          </BreadcrumbItem>
        </template>
      </BreadcrumbList>
    </Breadcrumb>
  </header>
</template>
