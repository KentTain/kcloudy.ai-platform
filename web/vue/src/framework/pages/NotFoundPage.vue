<script setup lang="ts">
import { useRouter } from "vue-router";
import { Button } from "@/components";

const router = useRouter();

const goBack = () => router.back();
const goHome = () => router.push("/");
</script>

<template>
  <div class="error-page">
    <div class="error-page__content">
      <h1 class="error-page__code error-page__code--primary">404</h1>
      <h2 class="error-page__title">页面不存在</h2>
      <p class="error-page__desc">抱歉，您访问的页面不存在</p>
      <div class="error-page__actions">
        <Button variant="outline" @click="goBack">返回上一页</Button>
        <Button @click="goHome">返回首页</Button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--color-surface);
}

.error-page__content {
  text-align: center;
}

.error-page__code {
  font-size: 6rem;
  font-weight: 700;
  margin: 0;
}

.error-page__code--danger {
  color: var(--color-danger);
}

.error-page__code--primary {
  color: var(--color-primary);
}

.error-page__title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 1rem 0 0.5rem;
}

.error-page__desc {
  color: var(--color-text-muted);
  margin: 0 0 2rem;
}

.error-page__actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
</style>