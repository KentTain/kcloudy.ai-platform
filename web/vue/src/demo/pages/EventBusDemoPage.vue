<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getEventBus, ModuleEvents } from "@/framework/events";
import type { EventHandler } from "@/framework/events";

interface EventLog {
  id: number;
  event: string;
  payload: unknown;
  timestamp: Date;
}

const eventBus = getEventBus();
const logs = ref<EventLog[]>([]);
const counter = ref(0);

// 定义事件处理器
let loggedInHandler: EventHandler;
let loggedOutHandler: EventHandler;
let tenantChangedHandler: EventHandler;
let dataRefreshHandler: EventHandler;

// 添加日志
function addLog(event: string, payload: unknown) {
  logs.value.unshift({
    id: Date.now(),
    event,
    payload,
    timestamp: new Date(),
  });
  // 保留最近 20 条日志
  if (logs.value.length > 20) {
    logs.value.pop();
  }
}

// 发布自定义事件
function emitCustomEvent() {
  counter.value++;
  eventBus.emit("demo:custom-event", {
    message: "自定义事件触发",
    count: counter.value,
  });
}

// 模拟用户登录
function simulateLogin() {
  const user = { id: 1, name: "演示用户", email: "demo@example.com" };
  eventBus.emit(ModuleEvents.USER_LOGGED_IN, user);
}

// 模拟用户登出
function simulateLogout() {
  eventBus.emit(ModuleEvents.USER_LOGGED_OUT);
}

// 模拟租户切换
function simulateTenantChange() {
  const tenant = { id: "tenant-001", name: "演示租户" };
  eventBus.emit(ModuleEvents.TENANT_CHANGED, tenant);
}

// 请求刷新数据
function requestRefresh() {
  eventBus.emit(ModuleEvents.DATA_REFRESH_REQUESTED, { source: "EventBusDemo" });
}

// 清空日志
function clearLogs() {
  logs.value = [];
}

onMounted(() => {
  // 订阅预定义事件
  loggedInHandler = (payload) => {
    addLog(ModuleEvents.USER_LOGGED_IN, payload);
  };
  loggedOutHandler = () => {
    addLog(ModuleEvents.USER_LOGGED_OUT, null);
  };
  tenantChangedHandler = (payload) => {
    addLog(ModuleEvents.TENANT_CHANGED, payload);
  };
  dataRefreshHandler = (payload) => {
    addLog(ModuleEvents.DATA_REFRESH_REQUESTED, payload);
  };

  // 订阅事件，获取取消订阅函数
  const unsubscribes = [
    eventBus.on(ModuleEvents.USER_LOGGED_IN, loggedInHandler),
    eventBus.on(ModuleEvents.USER_LOGGED_OUT, loggedOutHandler),
    eventBus.on(ModuleEvents.TENANT_CHANGED, tenantChangedHandler),
    eventBus.on(ModuleEvents.DATA_REFRESH_REQUESTED, dataRefreshHandler),
    // 订阅自定义事件
    eventBus.on("demo:custom-event", (payload) => {
      addLog("demo:custom-event", payload);
    }),
  ];

  // 存储取消订阅函数，组件卸载时调用
  onUnmounted(() => {
    unsubscribes.forEach((unsubscribe) => unsubscribe());
  });
});
</script>

<template>
  <AppPage title="EventBus 示例" eyebrow="Demo" description="演示事件总线的发布订阅模式">
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- 发布事件区域 -->
      <Card>
        <CardHeader>
          <CardTitle>发布事件</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <p class="text-muted-foreground text-sm">预定义事件</p>
            <div class="flex flex-wrap gap-2">
              <Button variant="outline" @click="simulateLogin">模拟登录</Button>
              <Button variant="outline" @click="simulateLogout">模拟登出</Button>
              <Button variant="outline" @click="simulateTenantChange">切换租户</Button>
              <Button variant="outline" @click="requestRefresh">刷新数据</Button>
            </div>
          </div>

          <div class="space-y-2">
            <p class="text-muted-foreground text-sm">自定义事件</p>
            <div class="flex gap-2">
              <Button @click="emitCustomEvent">触发自定义事件</Button>
              <span class="text-muted-foreground flex items-center text-sm">
                计数: {{ counter }}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 使用说明 -->
      <Card>
        <CardHeader>
          <CardTitle>使用说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-3 text-sm">
            <div>
              <code class="bg-muted rounded px-1">getEventBus()</code>
              <p class="text-muted-foreground mt-1">获取全局事件总线实例</p>
            </div>
            <div>
              <code class="bg-muted rounded px-1">eventBus.on(event, handler)</code>
              <p class="text-muted-foreground mt-1">订阅事件，返回取消订阅函数</p>
            </div>
            <div>
              <code class="bg-muted rounded px-1">eventBus.emit(event, payload)</code>
              <p class="text-muted-foreground mt-1">发布事件，传递数据</p>
            </div>
            <div>
              <code class="bg-muted rounded px-1">ModuleEvents</code>
              <p class="text-muted-foreground mt-1">预定义事件常量</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 事件日志 -->
      <Card class="lg:col-span-2">
        <CardHeader class="flex flex-row items-center justify-between">
          <CardTitle>事件日志</CardTitle>
          <Button variant="ghost" size="sm" @click="clearLogs">清空</Button>
        </CardHeader>
        <CardContent>
          <div v-if="logs.length === 0" class="text-muted-foreground py-8 text-center text-sm">
            暂无事件日志，请点击上方按钮发布事件
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="log in logs"
              :key="log.id"
              class="bg-muted/50 flex items-center justify-between rounded-lg p-3 text-sm"
            >
              <div class="flex items-center gap-3">
                <span class="bg-primary/10 text-primary rounded px-2 py-0.5 font-mono text-xs">
                  {{ log.event }}
                </span>
                <span class="text-muted-foreground">
                  {{ log.payload ? JSON.stringify(log.payload) : "无数据" }}
                </span>
              </div>
              <span class="text-muted-foreground text-xs">
                {{ log.timestamp.toLocaleTimeString() }}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </AppPage>
</template>
