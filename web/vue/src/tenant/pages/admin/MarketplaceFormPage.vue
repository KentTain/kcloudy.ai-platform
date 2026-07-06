<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getMarketplace, createMarketplace, updateMarketplace } from "@/tenant/api/marketplace";
import type { MarketplaceCreate, MarketplaceUpdate } from "@/tenant/types/marketplace";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import { Button, Input, Label, Card, Switch } from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, Save } from "@lucide/vue";

const route = useRoute();
const router = useRouter();

const marketplaceId = computed(() => route.params.id as string);
const isEdit = computed(() => !!marketplaceId.value);
const loading = ref(false);
const saving = ref(false);

// 表单数据
const form = ref({
  name: "",
  code: "",
  type: "dify",
  url: "",
  description: "",
  is_enabled: true,
});

// 表单验证错误
const errors = ref<Record<string, string>>({});

// 市场类型选项（与后端适配器类型对齐）
const typeOptions = [
  { value: "dify", label: "Dify 市场" },
  { value: "modelscope", label: "ModelScope 市场" },
  { value: "agentskills", label: "AgentSkills 市场" },
  { value: "modelscope-skill", label: "ModelScope Skill" },
  { value: "local-skill", label: "本地 Skill 目录" },
  { value: "local-plugin", label: "本地 Plugin 目录" },
];

// 是否为本地类型（使用路径而非 URL）
const isLocalType = computed(
  () => form.value.type === "local-skill" || form.value.type === "local-plugin",
);

// URL 字段占位符
const urlPlaceholder = computed(() =>
  isLocalType.value ? "例如: /data/plugins 或 file:///data/plugins" : "例如: https://marketplace.dify.ai",
);

// 加载市场详情（编辑模式）
const loadMarketplace = async () => {
  if (!isEdit.value) return;

  loading.value = true;
  try {
    const response = await getMarketplace(marketplaceId.value);
    if (response.data) {
      const data = response.data;
      form.value = {
        name: data.name,
        code: data.code,
        type: data.type || "dify",
        url: data.url,
        description: data.description || "",
        is_enabled: data.is_enabled,
      };
    }
  } catch (error) {
    console.error("加载市场详情失败:", error);
    notifyError("加载市场详情失败");
  } finally {
    loading.value = false;
  }
};

// 验证表单
const validateForm = (): boolean => {
  errors.value = {};

  if (!form.value.name.trim()) {
    errors.value.name = "请输入市场名称";
  }

  if (!form.value.code.trim()) {
    errors.value.code = "请输入市场编码";
  } else if (!/^[a-z][a-z0-9_-]*$/.test(form.value.code)) {
    errors.value.code = "市场编码必须以小写字母开头，只能包含小写字母、数字、下划线和连字符";
  }

  if (!form.value.url.trim()) {
    errors.value.url = isLocalType.value ? "请输入目录路径" : "请输入市场地址";
  } else if (!isLocalType.value) {
    try {
      new URL(form.value.url);
    } catch {
      errors.value.url = "请输入有效的 URL 地址";
    }
  }

  return Object.keys(errors.value).length === 0;
};

// 保存市场
const handleSave = async () => {
  if (!validateForm()) return;

  saving.value = true;
  try {
    if (isEdit.value) {
      const payload: MarketplaceUpdate = {
        name: form.value.name,
        url: form.value.url,
        description: form.value.description || undefined,
        is_enabled: form.value.is_enabled,
      };
      await updateMarketplace(marketplaceId.value, payload);
      notifySuccess("市场已更新");
    } else {
      const payload: MarketplaceCreate = {
        name: form.value.name,
        code: form.value.code,
        type: form.value.type,
        url: form.value.url,
        description: form.value.description || undefined,
      };
      await createMarketplace(payload);
      notifySuccess("市场已创建");
    }
    router.push("/admin/marketplaces");
  } catch (error: any) {
    console.error("保存市场失败:", error);
    const errorMessage = error?.response?.data?.msg || error?.message || "保存失败";
    notifyError(errorMessage);
  } finally {
    saving.value = false;
  }
};

// 返回列表
const handleBack = () => {
  router.push("/admin/marketplaces");
};

onMounted(() => {
  loadMarketplace();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="marketplace-form-page">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" data-testid="back-btn" @click="handleBack">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold">{{ isEdit ? "编辑市场" : "添加市场" }}</h2>
          <p class="text-muted-foreground mt-1 text-sm">
            {{ isEdit ? "修改市场配置信息" : "添加新的插件市场配置" }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" data-testid="cancel-btn" @click="handleBack">取消</Button>
        <Button data-testid="save-btn" :disabled="saving" @click="handleSave">
          <Save class="mr-1 h-4 w-4" />
          {{ saving ? "保存中..." : "保存" }}
        </Button>
      </div>
    </div>

    <!-- 表单区域 -->
    <Card class="flex min-h-0 flex-1 flex-col overflow-hidden p-6">
      <div v-if="loading" class="flex flex-col gap-4">
        <div v-for="n in 5" :key="n" class="space-y-2">
          <div class="h-4 w-20 bg-muted animate-pulse rounded" />
          <div class="h-10 w-full bg-muted animate-pulse rounded" />
        </div>
      </div>

      <div v-else class="mx-auto w-full max-w-2xl space-y-6">
        <!-- 市场名称 -->
        <div class="space-y-2">
          <Label for="name">市场名称 <span class="text-destructive">*</span></Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="例如: Dify 官方插件市场"
            data-testid="name-input"
            :class="{ 'border-destructive': errors.name }"
          />
          <p v-if="errors.name" class="text-destructive text-xs">{{ errors.name }}</p>
        </div>

        <!-- 市场编码 -->
        <div class="space-y-2">
          <Label for="code">市场编码 <span class="text-destructive">*</span></Label>
          <Input
            id="code"
            v-model="form.code"
            placeholder="例如: dify_official"
            data-testid="code-input"
            :disabled="isEdit"
            :class="{ 'border-destructive': errors.code }"
          />
          <p v-if="errors.code" class="text-destructive text-xs">{{ errors.code }}</p>
          <p v-else class="text-muted-foreground text-xs">
            市场编码只能包含小写字母、数字、下划线和连字符，创建后不可修改
          </p>
        </div>

        <!-- 市场类型 -->
        <div class="space-y-2">
          <Label for="type">市场类型</Label>
          <Select v-model="form.type" :disabled="isEdit">
            <SelectTrigger data-testid="type-select">
              <SelectValue placeholder="选择市场类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="option in typeOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>
          <p class="text-muted-foreground text-xs">
            选择市场适配器类型。本地类型扫描服务器目录，远程类型连接外部市场 API
          </p>
        </div>

        <!-- 市场地址 -->
        <div class="space-y-2">
          <Label for="url">{{ isLocalType ? '目录路径' : '市场地址' }} <span class="text-destructive">*</span></Label>
          <Input
            id="url"
            v-model="form.url"
            :placeholder="urlPlaceholder"
            data-testid="url-input"
            :class="{ 'border-destructive': errors.url }"
          />
          <p v-if="errors.url" class="text-destructive text-xs">{{ errors.url }}</p>
          <p v-else class="text-muted-foreground text-xs">
            {{ isLocalType ? '本地插件包或 Skill 文件所在的目录路径' : '插件市场的 API 地址，需要支持对应市场协议' }}
          </p>
        </div>

        <!-- 描述 -->
        <div class="space-y-2">
          <Label for="description">描述</Label>
          <textarea
            id="description"
            v-model="form.description"
            class="border-input placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[80px] w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请输入市场描述"
            data-testid="description-input"
            rows="3"
          />
        </div>

        <!-- 是否启用 -->
        <div class="flex items-center justify-between rounded-lg border p-4">
          <div class="space-y-0.5">
            <Label for="is_enabled">是否启用</Label>
            <p class="text-muted-foreground text-xs">启用后可以在市场中浏览和同步插件</p>
          </div>
          <Switch
            id="is_enabled"
            v-model:checked="form.is_enabled"
            data-testid="is-enabled-switch"
          />
        </div>
      </div>
    </Card>
  </div>
</template>
