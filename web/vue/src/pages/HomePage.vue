<script setup lang="ts">
</script>

<template>
  <div class="p-8">
    <div class="mx-auto max-w-4xl">
      <h1 class="mb-8 text-3xl font-bold text-gray-800">欢迎使用 Demo AI 助手平台</h1>

      <div class="mb-8">
        <AppCard title="快速开始">
          <p class="mb-4 text-gray-600">
            这是一个最小化的 AI 助手平台演示项目，展示前后端集成的核心功能。
          </p>
          <div class="flex gap-4">
            <RouterLink to="/datasets">
              <AppButton>查看知识库</AppButton>
            </RouterLink>
            <RouterLink to="/demo">
              <AppButton variant="secondary">Demo 面板</AppButton>
            </RouterLink>
          </div>
        </AppCard>
      </div>

      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <AppCard title="知识库管理">
          <p class="text-gray-600">
            创建和管理知识库，支持文档上传和向量化检索。
          </p>
        </AppCard>

        <AppCard title="AI 对话">
          <p class="text-gray-600">与 AI 助手进行智能对话，获取知识库中的相关信息。</p>
        </AppCard>
      </div>
    </div>
  </div>
</template>
