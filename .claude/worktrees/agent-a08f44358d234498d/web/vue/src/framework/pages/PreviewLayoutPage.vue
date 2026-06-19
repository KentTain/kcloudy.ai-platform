<script setup lang="ts">
/**
 * PreviewLayoutPage 布局预览页面
 * 无需登录，用于验证布局效果
 */
import { ref } from "vue";
import { Button } from "@/components";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AppPage from "@/framework/layouts/components/AppPage.vue";

const datasets = ref([
  { id: 1, name: "产品文档库", count: 128, updated: "2小时前", color: "from-emerald-500 to-emerald-600" },
  { id: 2, name: "FAQ 知识库", count: 256, updated: "1天前", color: "from-amber-500 to-amber-600" },
  { id: 3, name: "技术规范库", count: 64, updated: "3天前", color: "from-blue-500 to-blue-600" },
]);
</script>

<template>
  <AppPage
    title="知识库管理"
    eyebrow="知识管理"
    description="管理系统的知识库资源，支持文档上传、向量化处理和智能检索"
  >
    <template #actions>
      <Button class="bg-gradient-to-r from-primary to-primary/80 shadow-sm">
        + 新建知识库
      </Button>
      <Button variant="outline">
        筛选
      </Button>
    </template>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="dataset in datasets"
        :key="dataset.id"
        class="hover:shadow-md transition-shadow cursor-pointer"
      >
        <CardHeader class="pb-3">
          <div class="flex items-center gap-3">
            <div
              :class="`w-11 h-11 rounded-xl bg-gradient-to-br ${dataset.color} flex items-center justify-center text-white`"
            >
              📚
            </div>
            <div>
              <CardTitle class="text-base">{{ dataset.name }}</CardTitle>
              <p class="text-xs text-muted-foreground mt-0.5">
                {{ dataset.count }} 个文档 · 更新于 {{ dataset.updated }}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground line-clamp-2">
            存储产品相关的技术文档、API 规格和使用指南，支持智能检索和问答。
          </p>
        </CardContent>
      </Card>
    </div>
  </AppPage>
</template>
