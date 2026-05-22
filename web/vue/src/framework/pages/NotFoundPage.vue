<script setup lang="ts">
/**
 * NotFoundPage 404 页面不存在
 */
import { useRouter } from "vue-router";
import AppButton from "@/components/ui/CommonButton.vue";

const router = useRouter();

const goBack = () => router.back();
const goHome = () => router.push("/");
</script>

<template>
  <div class="not-found-page">
    <div class="not-found-page__content">
      <h1 class="not-found-page__code">404</h1>
      <h2 class="not-found-page__title">页面不存在</h2>
      <p class="not-found-page__desc">抱歉，您访问的页面不存在</p>
      <div class="not-found-page__actions">
        <CommonButton variant="outline" @click="goBack">返回上一页</CommonButton>
        <CommonButton @click="goHome">返回首页</CommonButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--color-surface);
}

.not-found-page__content {
  text-align: center;
}

.not-found-page__code {
  font-size: 6rem;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0;
}

.not-found-page__title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 1rem 0 0.5rem;
}

.not-found-page__desc {
  color: var(--color-text-muted);
  margin: 0 0 2rem;
}

.not-found-page__actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
</style>
