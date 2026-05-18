<script setup lang="ts">
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-gray-50">
    <div class="text-center">
      <h1 class="mb-4 text-6xl font-bold text-gray-300">404</h1>
      <p class="mb-8 text-xl text-gray-600">页面未找到</p>
      <RouterLink to="/">
        <AppButton>返回首页</AppButton>
      </RouterLink>
    </div>
  </div>
</template>
