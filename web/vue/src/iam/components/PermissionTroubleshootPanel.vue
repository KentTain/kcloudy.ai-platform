<script setup lang="ts">
/**
 * PermissionTroubleshootPanel — 权限排障面板组件
 *
 * 展示权限检查结果详情，包含：
 * - 请求信息（资源、操作、用户）
 * - 检查结果（允许/拒绝）
 * - 命中策略列表
 * - 拒绝原因详情
 */

import { computed } from "vue"
import { ShieldCheck, ShieldX, AlertTriangle } from "@lucide/vue"
import {
  Badge,
  DescriptionList,
} from "@/components"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

/** 策略命中信息 */
export interface PolicyHitInfo {
  policy_id: string;
  policy_name: string;
  type: "allow" | "deny";
  reason?: string;
  priority?: number;
}

/** 权限检查结果 */
export interface PermissionCheckResult {
  /** 检查的资源 */
  resource: string;
  /** 检查的操作 */
  action: string;
  /** 检查结果 */
  allowed: boolean;
  /** 拒绝原因 */
  deny_reason?: string;
  /** 命中的策略列表 */
  hit_policies: PolicyHitInfo[];
  /** 额外信息 */
  details?: Record<string, unknown>;
}

const props = defineProps<{
  /** 权限检查结果数据 */
  result: PermissionCheckResult;
}>()

// ========== 计算属性 ==========

/** 允许策略列表 */
const allowPolicies = computed(() =>
  props.result.hit_policies.filter((p) => p.type === "allow")
)

/** 拒绝策略列表 */
const denyPolicies = computed(() =>
  props.result.hit_policies.filter((p) => p.type === "deny")
)

/** 基本信息描述列表 */
const descriptionItems = computed(() => [
  { label: "资源", value: props.result.resource },
  { label: "操作", value: props.result.action },
  { label: "结果", value: props.result.allowed ? "允许" : "拒绝" },
  ...(props.result.deny_reason ? [{ label: "拒绝原因", value: props.result.deny_reason }] : []),
])
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- 检查结果概览 -->
    <div class="flex items-center gap-3 rounded-lg border p-4" :class="result.allowed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'">
      <component
        :is="result.allowed ? ShieldCheck : ShieldX"
        class="h-8 w-8 shrink-0"
        :class="result.allowed ? 'text-green-600' : 'text-red-600'"
      />
      <div>
        <p class="font-medium" :class="result.allowed ? 'text-green-800' : 'text-red-800'">
          {{ result.allowed ? "权限检查通过" : "权限被拒绝" }}
        </p>
        <p class="text-sm" :class="result.allowed ? 'text-green-700' : 'text-red-700'">
          {{ result.resource }}:{{ result.action }}
        </p>
      </div>
    </div>

    <!-- 基本信息 -->
    <div>
      <h4 class="mb-2 text-sm font-medium">基本信息</h4>
      <DescriptionList :items="descriptionItems" />
    </div>

    <!-- 命中策略 -->
    <div v-if="result.hit_policies.length > 0">
      <Separator class="mb-4" />
      <h4 class="mb-2 text-sm font-medium">命中策略（{{ result.hit_policies.length }}）</h4>

      <!-- 允许策略 -->
      <div v-if="allowPolicies.length > 0" class="mb-3">
        <p class="mb-1.5 text-xs text-muted-foreground">允许策略（{{ allowPolicies.length }}）</p>
        <ScrollArea class="max-h-[200px]">
          <div class="space-y-1.5">
            <div
              v-for="policy in allowPolicies"
              :key="policy.policy_id"
              class="flex items-center gap-2 rounded-md border border-green-200 bg-green-50/50 px-3 py-2"
            >
              <ShieldCheck class="h-4 w-4 shrink-0 text-green-600" />
              <span class="flex-1 text-sm font-medium">{{ policy.policy_name }}</span>
              <Badge v-if="policy.priority !== undefined" variant="outline" class="text-xs">
                P{{ policy.priority }}
              </Badge>
            </div>
          </div>
        </ScrollArea>
      </div>

      <!-- 拒绝策略 -->
      <div v-if="denyPolicies.length > 0">
        <p class="mb-1.5 text-xs text-muted-foreground">拒绝策略（{{ denyPolicies.length }}）</p>
        <ScrollArea class="max-h-[200px]">
          <div class="space-y-1.5">
            <div
              v-for="policy in denyPolicies"
              :key="policy.policy_id"
              class="flex flex-col gap-1 rounded-md border border-red-200 bg-red-50/50 px-3 py-2"
            >
              <div class="flex items-center gap-2">
                <ShieldX class="h-4 w-4 shrink-0 text-red-600" />
                <span class="flex-1 text-sm font-medium">{{ policy.policy_name }}</span>
                <Badge v-if="policy.priority !== undefined" variant="outline" class="text-xs">
                  P{{ policy.priority }}
                </Badge>
              </div>
              <p v-if="policy.reason" class="ml-6 text-xs text-red-700">
                {{ policy.reason }}
              </p>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>

    <!-- 无命中策略 -->
    <div v-else>
      <Separator class="mb-4" />
      <div class="flex items-center gap-2 text-muted-foreground">
        <AlertTriangle class="h-4 w-4" />
        <span class="text-sm">无命中策略</span>
      </div>
    </div>

    <!-- 拒绝原因详情 -->
    <div v-if="!result.allowed && result.deny_reason">
      <Separator class="mb-4" />
      <h4 class="mb-2 text-sm font-medium">拒绝详情</h4>
      <div class="rounded-md border border-red-200 bg-red-50/50 p-3">
        <p class="text-sm text-red-800">{{ result.deny_reason }}</p>
      </div>
    </div>

    <!-- 额外信息 -->
    <div v-if="result.details && Object.keys(result.details).length > 0">
      <Separator class="mb-4" />
      <h4 class="mb-2 text-sm font-medium">额外信息</h4>
      <pre class="overflow-x-auto rounded-md bg-muted p-3 text-xs">{{ JSON.stringify(result.details, null, 2) }}</pre>
    </div>
  </div>
</template>
