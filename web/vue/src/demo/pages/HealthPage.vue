<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getHealth, type HealthStatus } from "@/demo/api/health";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

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
  <AppPage title="健康检查" variant="list">
    <div v-if="loading" class="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <Skeleton class="h-5 w-24" />
        </CardHeader>
        <CardContent class="flex flex-col gap-2">
          <Skeleton class="h-4 w-40" />
          <Skeleton class="h-4 w-64" />
        </CardContent>
      </Card>
    </div>

    <Card v-else-if="error">
      <CardHeader>
        <CardTitle>检查失败</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <p class="text-destructive text-sm">{{ error }}</p>
        <Button variant="outline" @click="fetchHealth">重试</Button>
      </CardContent>
    </Card>

    <Card v-else-if="healthStatus">
      <CardHeader>
        <CardTitle>服务状态</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-4">
        <div class="flex items-center gap-3">
          <span class="text-muted-foreground text-sm font-medium">状态</span>
          <Badge :variant="healthStatus.status === 'healthy' ? 'success' : 'destructive'">
            {{ healthStatus.status }}
          </Badge>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-muted-foreground text-sm font-medium">时间戳</span>
          <span class="font-mono text-sm">{{ healthStatus.timestamp }}</span>
        </div>
      </CardContent>
    </Card>

    <div v-if="!loading" class="mt-4">
      <Button variant="outline" @click="fetchHealth">刷新</Button>
    </div>
  </AppPage>
</template>