<script setup lang="ts">
/**
 * HealthPage 健康检查页面
 */
import { onMounted, ref } from "vue";
import { getHealth } from "@/demo/api/health";
import CommonCard from "@/components/CommonCard.vue";
import CommonButton from "@/components/CommonButton.vue";
import CommonLoading from "@/components/CommonLoading.vue";

interface HealthStatus {
  status: string;
  timestamp: string;
}

const healthStatus = ref<HealthStatus | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const fetchHealth = async () => {
  loading.value = true;
  error.value = null;

  try {
    healthStatus.value = await getHealth();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "健康检查失败";
  } finally {
    loading.value = false;
  }
};

onMounted(fetchHealth);
</script>

<template>
  <div class="health-page">
    <CommonCard title="健康检查">
      <div v-if="loading" class="health-page__loading">
        <CommonLoading text="检查中..." />
      </div>

      <div v-else-if="error" class="health-page__error">
        <p>{{ error }}</p>
        <CommonButton @click="fetchHealth">重试</CommonButton>
      </div>

      <div v-else-if="healthStatus" class="health-page__status">
        <div class="health-page__item">
          <span class="health-page__label">状态</span>
          <span :class="['health-page__value', 'health-page__value--success']">
            {{ healthStatus.status }}
          </span>
        </div>
        <div class="health-page__item">
          <span class="health-page__label">时间戳</span>
          <span class="health-page__value">{{ healthStatus.timestamp }}</span>
        </div>
      </div>

      <div class="health-page__actions">
        <CommonButton variant="outline" @click="fetchHealth">刷新</CommonButton>
      </div>
    </CommonCard>
  </div>
</template>

<style scoped>
.health-page__loading {
  padding: 2rem;
  text-align: center;
}

.health-page__error {
  padding: 1rem;
  text-align: center;
  color: var(--color-danger);
}

.health-page__error p {
  margin: 0 0 1rem;
}

.health-page__status {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.health-page__item {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.health-page__label {
  font-weight: 500;
  color: var(--color-text-muted);
  min-width: 80px;
}

.health-page__value {
  color: var(--color-text);
  font-family: var(--font-mono);
}

.health-page__value--success {
  color: var(--color-success);
}

.health-page__actions {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}
</style>
