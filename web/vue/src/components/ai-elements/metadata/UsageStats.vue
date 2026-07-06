<!-- src/components/ai-elements/metadata/UsageStats.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ThumbsUpIcon, ThumbsDownIcon } from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components'
import { get } from '@/framework/api/client'

const startDate = ref<Date>()
const endDate = ref<Date>()

const stats = ref({
  totalMessages: 0,
  totalTokens: 0,
  totalCost: 0,
  avgResponseTimeMs: 0,
  ratingDistribution: {} as Record<number, number>,
  modelDistribution: {} as Record<string, number>,
})

const fetchStats = async () => {
  stats.value = await get<typeof stats.value>('/ai/console/v1/metadata/usage-stats', {
    params: {
      start_date: startDate.value?.toISOString(),
      end_date: endDate.value?.toISOString(),
    },
  })
}

onMounted(fetchStats)

const formatNumber = (num: number): string => {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`
  return num.toString()
}
</script>

<template>
  <div class="space-y-6">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">
            总消息数
          </CardTitle>
        </CardHeader>
        <CardContent data-testid="total-messages">
          <div class="text-2xl font-bold">{{ stats.totalMessages }}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">
            总 Token 数
          </CardTitle>
        </CardHeader>
        <CardContent data-testid="total-tokens">
          <div class="text-2xl font-bold">{{ formatNumber(stats.totalTokens) }}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">
            总成本
          </CardTitle>
        </CardHeader>
        <CardContent data-testid="total-cost">
          <div class="text-2xl font-bold">${{ stats.totalCost.toFixed(2) }}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle class="text-sm font-medium text-muted-foreground">
            平均响应时间
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ stats.avgResponseTimeMs.toFixed(0) }}ms</div>
        </CardContent>
      </Card>
    </div>

    <!-- 评分分布 -->
    <Card>
      <CardHeader>
        <CardTitle>评分分布</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex items-center gap-8">
          <div class="flex items-center gap-2">
            <ThumbsUpIcon class="size-5 text-green-500" />
            <span class="font-medium">{{ stats.ratingDistribution[2] || 0 }}</span>
          </div>
          <div class="flex items-center gap-2">
            <ThumbsDownIcon class="size-5 text-red-500" />
            <span class="font-medium">{{ stats.ratingDistribution[1] || 0 }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 模型分布 -->
    <Card>
      <CardHeader>
        <CardTitle>模型使用分布</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-2">
          <div
            v-for="(count, model) in stats.modelDistribution"
            :key="model"
            class="flex items-center justify-between"
          >
            <span class="font-medium">{{ model }}</span>
            <Badge variant="secondary">{{ count }} 次</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
