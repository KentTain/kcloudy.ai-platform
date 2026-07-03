<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, Save, RefreshCw, Plus, Plug, Pencil, Trash2, ZapCircle, CheckCircle2, XCircle } from "lucide-vue-next";
import { Button, Card, Badge, Input, Textarea, Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components";
import { notifySuccess, notifyError, confirmAction } from "@/framework/utils/feedback";
import {
  getPluginConfig,
  updatePluginConfig,
  getPluginCredentials,
  deletePluginCredential,
  validateStoredCredential,
  type PluginConfigResponse,
  type PluginCredential,
} from "@/ai/api/plugin";
import { testPlugin, type TestPluginResponse } from "@/ai/api/pluginConfig";
import CredentialFormDialog from "@/ai/components/CredentialFormDialog.vue";

const route = useRoute();
const router = useRouter();
const pluginId = route.params.pluginId as string;

const loading = ref(true);
const saving = ref(false);
const config = ref<PluginConfigResponse | null>(null);

// 运行时配置（JSON 字符串）
const runtimeConfigJson = ref("");

const parsedRuntimeConfig = computed(() => {
  try {
    return JSON.parse(runtimeConfigJson.value || "{}");
  } catch {
    return null;
  }
});

const isJsonValid = computed(() => {
  try {
    JSON.parse(runtimeConfigJson.value || "{}");
    return true;
  } catch {
    return false;
  }
});

const hasChanges = computed(() => {
  if (!config.value) return false;
  try {
    const original = JSON.stringify(config.value.runtime_config || {}, null, 2);
    return runtimeConfigJson.value !== original;
  } catch {
    return false;
  }
});

// ===== 凭证管理 =====
const credentials = ref<PluginCredential[]>([]);
const credentialsLoading = ref(false);
const dialogOpen = ref(false);
const dialogMode = ref<"create" | "edit">("create");
const editingCredential = ref<PluginCredential | null>(null);
const testingCredentialId = ref<string | null>(null);
const noCredentialSchema = ref(false);

// ===== 测试连接 =====
const testingConnection = ref(false);
const testResult = ref<TestPluginResponse | null>(null);
const testDialogOpen = ref(false);

const loadConfig = async () => {
  loading.value = true;
  try {
    const response = await getPluginConfig(pluginId);
    if (response.data) {
      config.value = response.data;
      runtimeConfigJson.value = JSON.stringify(response.data.runtime_config || {}, null, 2);
    }
  } catch (error: any) {
    console.error("加载插件配置失败:", error);
    notifyError(error?.response?.data?.msg || "加载插件配置失败");
  } finally {
    loading.value = false;
  }
};

const loadCredentials = async () => {
  credentialsLoading.value = true;
  try {
    const response = await getPluginCredentials(pluginId);
    credentials.value = response.data || [];
  } catch {
    credentials.value = [];
  } finally {
    credentialsLoading.value = false;
  }
};

const handleBack = () => {
  router.push("/ai/plugins");
};

const handleReset = () => {
  if (config.value) {
    runtimeConfigJson.value = JSON.stringify(config.value.runtime_config || {}, null, 2);
  }
};

const handleSave = async () => {
  if (!isJsonValid.value) {
    notifyError("JSON 格式无效，请检查语法");
    return;
  }

  if (!hasChanges.value) {
    notifyError("未修改任何内容");
    return;
  }

  saving.value = true;
  try {
    const response = await updatePluginConfig(pluginId, {
      runtime_config: parsedRuntimeConfig.value,
    });
    if (response.data) {
      config.value = response.data;
      runtimeConfigJson.value = JSON.stringify(response.data.runtime_config || {}, null, 2);
      notifySuccess("配置已保存");
    }
  } catch (error: any) {
    console.error("保存配置失败:", error);
    notifyError(error?.response?.data?.msg || "保存配置失败");
  } finally {
    saving.value = false;
  }
};

const formatJson = () => {
  try {
    const parsed = JSON.parse(runtimeConfigJson.value || "{}");
    runtimeConfigJson.value = JSON.stringify(parsed, null, 2);
  } catch {
    // 格式化失败，保持原样
  }
};

// 测试插件配置连接
const handleTestConnection = async () => {
  testingConnection.value = true;
  testResult.value = null;
  try {
    const response = await testPlugin(pluginId);
    if (response.data) {
      testResult.value = response.data;
      testDialogOpen.value = true;
      if (response.data.validated) {
        notifySuccess("连接测试通过");
      } else {
        notifyError(`连接测试失败: ${response.data.message}`);
      }
    }
  } catch (error: any) {
    console.error("测试连接失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "测试连接失败";
    testResult.value = {
      plugin_id: pluginId,
      validated: false,
      message: errorMessage,
    };
    testDialogOpen.value = true;
    notifyError(errorMessage);
  } finally {
    testingConnection.value = false;
  }
};

// 凭证操作
const handleAddCredential = () => {
  dialogMode.value = "create";
  editingCredential.value = null;
  dialogOpen.value = true;
};

const handleEditCredential = (cred: PluginCredential) => {
  dialogMode.value = "edit";
  editingCredential.value = cred;
  dialogOpen.value = true;
};

const handleDeleteCredential = async (cred: PluginCredential) => {
  if (!confirmAction(`确定删除凭证"${cred.name}"吗？`)) return;
  try {
    await deletePluginCredential(pluginId, cred.id);
    notifySuccess("凭证已删除");
    loadCredentials();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "删除凭证失败");
  }
};

const handleTestCredential = async (cred: PluginCredential) => {
  testingCredentialId.value = cred.id;
  try {
    const response = await validateStoredCredential(pluginId, cred.id);
    if (response.data?.success) {
      notifySuccess("凭证验证通过");
    } else {
      notifyError(`凭证验证失败: ${response.data?.error || "未知错误"}`);
    }
  } catch (error: any) {
    notifyError(`凭证验证失败: ${error?.message || "未知错误"}`);
  } finally {
    testingCredentialId.value = null;
  }
};

const handleCredentialSaved = () => {
  loadCredentials();
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
};

onMounted(() => {
  loadConfig();
  loadCredentials();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-config-page">
    <!-- 页面标题区 -->
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="handleBack">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回列表
      </Button>
      <h2 class="text-xl font-semibold">插件配置</h2>
      <Badge v-if="config" variant="outline">{{ config.plugin_id }}</Badge>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">加载中...</div>
    </div>

    <!-- 配置内容 -->
    <template v-else-if="config">
      <!-- 插件能力配置（只读） -->
      <Card class="p-5">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">插件能力配置</h3>
            <Badge variant="secondary">只读</Badge>
          </div>
          <div class="min-h-0 overflow-auto rounded-md bg-muted/50 p-4">
            <pre class="text-xs font-mono whitespace-pre-wrap break-all">{{
              JSON.stringify(config.plugin_config, null, 2)
            }}</pre>
          </div>
        </div>
      </Card>

      <!-- 凭证配置 -->
      <Card class="p-5">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">凭证配置</h3>
            <Button variant="outline" size="sm" @click="handleAddCredential">
              <Plus class="mr-1 h-3.5 w-3.5" />
              新增凭证
            </Button>
          </div>

          <!-- 凭证列表 -->
          <div v-if="credentialsLoading" class="py-4 text-center text-muted-foreground text-sm">
            加载中...
          </div>
          <div v-else-if="credentials.length === 0" class="py-4 text-center text-muted-foreground text-sm">
            暂无凭证配置，点击"新增凭证"添加
          </div>
          <div v-else class="overflow-auto rounded-md border">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b bg-muted/50">
                  <th class="px-3 py-2 text-left font-medium">名称</th>
                  <th class="px-3 py-2 text-left font-medium">作用域</th>
                  <th class="px-3 py-2 text-left font-medium">创建时间</th>
                  <th class="px-3 py-2 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="cred in credentials"
                  :key="cred.id"
                  class="border-b last:border-b-0"
                >
                  <td class="px-3 py-2">{{ cred.name }}</td>
                  <td class="px-3 py-2">
                    <Badge variant="outline">{{ cred.scope || 'global' }}</Badge>
                  </td>
                  <td class="px-3 py-2 text-muted-foreground">{{ formatDate(cred.created_at) }}</td>
                  <td class="px-3 py-2 text-right">
                    <div class="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        :disabled="!!testingCredentialId"
                        @click="handleTestCredential(cred)"
                      >
                        <RefreshCw
                          v-if="testingCredentialId === cred.id"
                          class="h-3.5 w-3.5 animate-spin"
                        />
                        <Plug v-else class="h-3.5 w-3.5" />
                        测试
                      </Button>
                      <Button variant="ghost" size="sm" @click="handleEditCredential(cred)">
                        <Pencil class="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="sm" @click="handleDeleteCredential(cred)">
                        <Trash2 class="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      <!-- 运行时配置（可编辑） -->
      <Card class="flex min-h-0 flex-1 flex-col overflow-hidden p-5">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">运行时配置</h3>
            <div class="flex gap-2">
              <Button variant="outline" size="sm" @click="formatJson">
                格式化
              </Button>
              <Button variant="outline" size="sm" @click="handleReset" :disabled="!hasChanges">
                重置
              </Button>
            </div>
          </div>

          <!-- JSON 编辑器 -->
          <div class="space-y-2">
            <textarea
              v-model="runtimeConfigJson"
              class="min-h-[300px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              :class="{ 'border-destructive': !isJsonValid }"
              placeholder="{}"
              spellcheck="false"
            />
            <div v-if="!isJsonValid" class="text-destructive text-sm">
              JSON 格式无效，请检查语法
            </div>
          </div>
        </div>
      </Card>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-2">
        <Button variant="outline" @click="handleBack">取消</Button>
        <Button
          variant="outline"
          :disabled="testingConnection"
          @click="handleTestConnection"
        >
          <ZapCircle v-if="!testingConnection" class="mr-1 h-4 w-4" />
          <RefreshCw v-else class="mr-1 h-4 w-4 animate-spin" />
          {{ testingConnection ? "测试中..." : "测试连接" }}
        </Button>
        <Button
          :disabled="!hasChanges || !isJsonValid || saving"
          @click="handleSave"
        >
          <Save v-if="!saving" class="mr-1 h-4 w-4" />
          <RefreshCw v-else class="mr-1 h-4 w-4 animate-spin" />
          {{ saving ? "保存中..." : "保存配置" }}
        </Button>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-else class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">插件配置不存在</div>
    </div>

    <!-- 测试结果对话框 -->
    <Dialog v-model:open="testDialogOpen">
      <DialogContent class="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>连接测试结果</DialogTitle>
          <DialogDescription>
            插件「{{ pluginId }}」配置连接测试结果
          </DialogDescription>
        </DialogHeader>
        <div v-if="testResult" class="space-y-4 py-2">
          <div class="flex flex-col items-center gap-2">
            <CheckCircle2
              v-if="testResult.validated"
              class="h-12 w-12 text-green-500"
            />
            <XCircle v-else class="h-12 w-12 text-destructive" />
            <div
              class="text-lg font-medium"
              :class="testResult.validated ? 'text-green-600' : 'text-destructive'"
            >
              {{ testResult.validated ? "连接成功" : "连接失败" }}
            </div>
          </div>
          <div class="rounded-md bg-muted/50 p-3">
            <div class="text-sm text-muted-foreground">详细消息</div>
            <div class="mt-1 text-sm break-all">{{ testResult.message }}</div>
          </div>
        </div>
        <DialogFooter>
          <Button @click="testDialogOpen = false">关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 凭证编辑弹窗 -->
    <CredentialFormDialog
      v-model:open="dialogOpen"
      :plugin-id="pluginId"
      :mode="dialogMode"
      :credential="editingCredential"
      @saved="handleCredentialSaved"
    />
  </div>
</template>
