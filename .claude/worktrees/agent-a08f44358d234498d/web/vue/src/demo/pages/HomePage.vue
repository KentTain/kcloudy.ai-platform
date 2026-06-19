<script setup lang="ts">
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  { title: "设计令牌系统", desc: "基于 Tailwind CSS v4 @theme 指令，蔚蓝主色 + 橙红辅色" },
  { title: "AdminLayout 布局", desc: "侧边栏 + 顶部导航 + TagsView + 内容区" },
  { title: "UI 组件库", desc: "Button、Input、Card、Modal、Loading 等基础组件" },
  { title: "权限控制", desc: "动态路由 + v-permission 指令 + 接口拦截" },
];
</script>

<template>
  <AppPage title="欢迎使用 AI 助手平台" variant="list">
    <p class="text-muted-foreground text-sm">这是一个基于 Vue 3 + TypeScript + Vite 构建的后台管理系统演示项目。</p>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card v-for="feature in features" :key="feature.title">
        <CardHeader>
          <CardTitle class="text-primary">{{ feature.title }}</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-muted-foreground text-sm">{{ feature.desc }}</p>
        </CardContent>
      </Card>
    </div>
  </AppPage>
</template>