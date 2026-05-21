<script setup lang="ts">
/**
 * HomePage 首页
 */
import AppCard from "@/framework/components/ui/AppCard.vue";
</script>

<template>
  <div class="home-page">
    <AppCard title="欢迎使用 AI 助手平台">
      <p class="home-page__desc">
        这是一个基于 Vue 3 + TypeScript + Vite 构建的后台管理系统演示项目。
      </p>
      <div class="home-page__features">
        <div class="home-page__feature">
          <h3>设计令牌系统</h3>
          <p>基于 Tailwind CSS v4 @theme 指令，蔚蓝主色 + 橙红辅色</p>
        </div>
        <div class="home-page__feature">
          <h3>AdminLayout 布局</h3>
          <p>侧边栏 + 顶部导航 + TagsView + 内容区</p>
        </div>
        <div class="home-page__feature">
          <h3>UI 组件库</h3>
          <p>Button、Input、Card、Modal、Loading 等基础组件</p>
        </div>
        <div class="home-page__feature">
          <h3>权限控制</h3>
          <p>动态路由 + v-permission 指令 + 接口拦截</p>
        </div>
      </div>
    </AppCard>
  </div>
</template>

<style scoped>
.home-page__desc {
  color: var(--color-text-muted);
  margin-bottom: 1.5rem;
}

.home-page__features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.home-page__feature {
  padding: 1rem;
  background-color: var(--color-surface);
  border-radius: var(--radius-ui);
}

.home-page__feature h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  color: var(--color-primary);
}

.home-page__feature p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}
</style>
