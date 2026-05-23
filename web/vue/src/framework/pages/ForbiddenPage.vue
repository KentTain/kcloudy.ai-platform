<script setup lang="ts">
/**
 * ForbiddenPage 403 无权限页面
 */
import { useRouter } from "vue-router";
import AppButton from "@/components/CommonButton.vue";

const router = useRouter();

const goBack = () => router.back();
const goHome = () => router.push("/");
</script>

<template>
  <div class="forbidden-page">
    <div class="forbidden-page__content">
      <h1 class="forbidden-page__code">403</h1>
      <h2 class="forbidden-page__title">无访问权限</h2>
      <p class="forbidden-page__desc">抱歉，您没有权限访问此页面</p>
      <div class="forbidden-page__actions">
        <CommonButton variant="outline" @click="goBack">返回上一页</CommonButton>
        <CommonButton @click="goHome">返回首页</CommonButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forbidden-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--color-surface);
}

.forbidden-page__content {
  text-align: center;
}

.forbidden-page__code {
  font-size: 6rem;
  font-weight: 700;
  color: var(--color-danger);
  margin: 0;
}

.forbidden-page__title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 1rem 0 0.5rem;
}

.forbidden-page__desc {
  color: var(--color-text-muted);
  margin: 0 0 2rem;
}

.forbidden-page__actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
</style>
