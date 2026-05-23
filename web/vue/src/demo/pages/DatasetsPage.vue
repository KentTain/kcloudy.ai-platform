<script setup lang="ts">
/**
 * DatasetsPage 知识库列表页面
 */
import { onMounted, ref, computed } from "vue";
import { useDatasetStore } from "@/demo/stores/datasets";
import CommonCard from "@/components/CommonCard.vue";
import CommonButton from "@/components/CommonButton.vue";
import CommonLoading from "@/components/CommonLoading.vue";

const datasetStore = useDatasetStore();

const loading = computed(() => datasetStore.loading);
const error = computed(() => datasetStore.error);
const datasets = computed(() => datasetStore.datasets);

onMounted(() => {
  datasetStore.fetchDatasets();
});
</script>

<template>
  <div class="datasets-page">
    <CommonCard title="知识库列表">
      <template #header>
        <div class="datasets-page__header">
          <h3>知识库列表</h3>
          <CommonButton size="sm">新建知识库</CommonButton>
        </div>
      </template>

      <div v-if="loading" class="datasets-page__loading">
        <CommonLoading text="加载中..." />
      </div>

      <div v-else-if="error" class="datasets-page__error">
        <p>{{ error }}</p>
        <CommonButton @click="datasetStore.fetchDatasets">重试</CommonButton>
      </div>

      <div v-else-if="datasets.length === 0" class="datasets-page__empty">
        <p>暂无知识库</p>
      </div>

      <div v-else class="datasets-page__list">
        <div v-for="item in datasets" :key="item.id" class="datasets-page__item">
          <div class="datasets-page__item-info">
            <h4 class="datasets-page__item-name">{{ item.name }}</h4>
            <p class="datasets-page__item-desc">{{ item.description || "暂无描述" }}</p>
          </div>
          <div class="datasets-page__item-actions">
            <CommonButton size="sm" variant="outline">查看</CommonButton>
            <CommonButton size="sm" variant="ghost">删除</CommonButton>
          </div>
        </div>
      </div>
    </CommonCard>
  </div>
</template>

<style scoped>
.datasets-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.datasets-page__header h3 {
  margin: 0;
}

.datasets-page__loading {
  padding: 2rem;
  text-align: center;
}

.datasets-page__error {
  padding: 1rem;
  text-align: center;
  color: var(--color-danger);
}

.datasets-page__empty {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
}

.datasets-page__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.datasets-page__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background-color: var(--color-surface);
  border-radius: var(--radius-ui);
  transition: background-color var(--transition-fast);
}

.datasets-page__item:hover {
  background-color: var(--color-primary-subtle);
}

.datasets-page__item-info {
  flex: 1;
}

.datasets-page__item-name {
  margin: 0 0 0.25rem;
  font-size: 0.875rem;
  color: var(--color-text);
}

.datasets-page__item-desc {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.datasets-page__item-actions {
  display: flex;
  gap: 0.5rem;
}
</style>
