<script setup lang="ts">
/**
 * 模型配置 - 设置默认模型弹窗
 *
 * 两种模式：
 * - LLM：单选
 * - Embedding/Rerank：联动选择，必须来自同一插件
 */
import { ref, computed, watch } from "vue";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  Button,
  Badge,
} from "@/components";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Loader2, AlertTriangle } from "lucide-vue-next";
import { notifySuccess, notifyError, confirmAction } from "@/framework/utils/feedback";
import { getModelsByType, batchSetDefaultModels } from "@/ai/api/modelConfig";
import type { ModelSelectItem, DefaultModelItem, ModelTypeKey } from "@/ai/types/modelConfig";
import { MODEL_TYPE_LABELS } from "@/ai/types/modelConfig";

const props = defineProps<{
  open: boolean;
  modelType: "llm" | "embedding-rerank";
  currentDefault?: DefaultModelItem;
  pluginId?: string;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
  (e: "saved"): void;
}>();

const loading = ref(false);
const saving = ref(false);

// LLM 模式
const llmModels = ref<ModelSelectItem[]>([]);
const selectedLlm = ref<string>("");

// Embedding/Rerank 模式
const embeddingModels = ref<ModelSelectItem[]>([]);
const rerankModels = ref<ModelSelectItem[]>([]);
const selectedEmbedding = ref<string>("");
const selectedRerank = ref<string>("");

// 已有默认模型提示
const hasExistingDefault = computed(() => {
  if (props.modelType === "llm") {
    return !!props.currentDefault?.model_name;
  }
  return !!props.currentDefault?.model_name;
});

// 联动逻辑：选中 embedding 后，rerank 非同插件的选项禁用
const selectedEmbeddingItem = computed(() =>
  embeddingModels.value.find((m) => `${m.plugin_id}|${m.model_name}` === selectedEmbedding.value),
);

const selectedRerankItem = computed(() =>
  rerankModels.value.find((m) => `${m.plugin_id}|${m.model_name}` === selectedRerank.value),
);

function isRerankDisabled(model: ModelSelectItem): boolean {
  if (!selectedEmbedding.value) return false;
  return model.plugin_id !== selectedEmbeddingItem.value?.plugin_id;
}

function isEmbeddingDisabled(model: ModelSelectItem): boolean {
  if (!selectedRerank.value) return false;
  return model.plugin_id !== selectedRerankItem.value?.plugin_id;
}

// 供应商推荐标记
function isRecommended(model: ModelSelectItem, otherItem?: ModelSelectItem): boolean {
  if (!otherItem) return false;
  return model.plugin_id === otherItem.plugin_id && model.provider === otherItem.provider;
}

// 提交校验
const canSubmit = computed(() => {
  if (props.modelType === "llm") {
    return !!selectedLlm.value;
  }
  if (!selectedEmbedding.value || !selectedRerank.value) return false;
  // 必须同插件
  return selectedEmbeddingItem.value?.plugin_id === selectedRerankItem.value?.plugin_id;
});

// 缺少模型校验
const missingModelType = computed<string | null>(() => {
  if (props.modelType !== "embedding-rerank") return null;
  if (embeddingModels.value.length === 0) return "text-embedding";
  if (rerankModels.value.length === 0) return "rerank";
  return null;
});

async function loadModels() {
  loading.value = true;
  try {
    if (props.modelType === "llm") {
      const data = await getModelsByType("llm");
      llmModels.value = data;
    } else {
      const [emb, rerank] = await Promise.all([
        getModelsByType("text-embedding"),
        getModelsByType("rerank"),
      ]);
      embeddingModels.value = emb;
      rerankModels.value = rerank;
    }
  } catch {
    notifyError("获取模型列表失败");
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.open,
  (val) => {
    if (val) {
      selectedLlm.value = "";
      selectedEmbedding.value = "";
      selectedRerank.value = "";
      loadModels();
    }
  },
);

function getModelKey(m: ModelSelectItem): string {
  return `${m.plugin_id}|${m.model_name}`;
}

// 按 plugin_id 分组
function groupByPlugin(models: ModelSelectItem[]): Record<string, ModelSelectItem[]> {
  const grouped: Record<string, ModelSelectItem[]> = {};
  for (const m of models) {
    if (!grouped[m.plugin_id]) grouped[m.plugin_id] = [];
    grouped[m.plugin_id].push(m);
  }
  return grouped;
}

async function handleSave() {
  // LLM 模式且已有默认模型时，需要用户确认覆盖
  if (props.modelType === "llm" && hasExistingDefault.value) {
    const confirmed = confirmAction(
      `当前默认模型为「${props.currentDefault?.model_name}」，确定要覆盖为新的默认模型吗？`,
    );
    if (!confirmed) return;
  }

  saving.value = true;
  try {
    if (props.modelType === "llm") {
      const model = llmModels.value.find((m) => getModelKey(m) === selectedLlm.value);
      if (!model) return;
      await batchSetDefaultModels({
        items: [
          {
            model_type: "llm",
            plugin_id: model.plugin_id,
            model_name: model.model_name,
          },
        ],
      });
    } else {
      const emb = embeddingModels.value.find((m) => getModelKey(m) === selectedEmbedding.value);
      const rerank = rerankModels.value.find((m) => getModelKey(m) === selectedRerank.value);
      if (!emb || !rerank) return;
      await batchSetDefaultModels({
        items: [
          {
            model_type: "text-embedding",
            plugin_id: emb.plugin_id,
            model_name: emb.model_name,
          },
          {
            model_type: "rerank",
            plugin_id: rerank.plugin_id,
            model_name: rerank.model_name,
          },
        ],
      });
    }
    notifySuccess("默认模型设置成功");
    emit("update:open", false);
    emit("saved");
  } catch (e: any) {
    const msg = e?.response?.data?.msg || e?.message || "设置失败";
    notifyError(msg);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[600px]">
      <DialogHeader>
        <DialogTitle>
          {{ modelType === "llm" ? "设置默认 LLM 模型" : "设置默认 Embedding & Rerank 模型" }}
        </DialogTitle>
        <DialogDescription>
          {{ modelType === "llm" ? "选择一个 LLM 模型作为默认模型" : "同时设置嵌入和排序的默认模型，两者必须来自同一插件" }}
        </DialogDescription>
      </DialogHeader>

      <!-- 已有默认模型提示（仅 embedding/rerank 模式） -->
      <div
        v-if="hasExistingDefault && modelType === 'embedding-rerank'"
        class="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
      >
        <AlertTriangle class="h-4 w-4 shrink-0" />
        <span>当前已有默认模型「{{ currentDefault?.model_name }}」，设置后不可更改</span>
      </div>

      <!-- LLM 已有默认模型提示（可覆盖） -->
      <div
        v-if="hasExistingDefault && modelType === 'llm'"
        class="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800"
      >
        <span>当前默认模型为「{{ currentDefault?.model_name }}」，选择新模型将覆盖当前默认</span>
      </div>

      <!-- 缺少模型提示 -->
      <div
        v-if="missingModelType"
        class="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800"
      >
        <AlertTriangle class="h-4 w-4 shrink-0" />
        <span>请先在插件下配置 {{ MODEL_TYPE_LABELS[missingModelType as ModelTypeKey] }} 类型的模型</span>
      </div>

      <div v-if="loading" class="flex items-center justify-center py-8">
        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
      </div>

      <!-- LLM 单选模式 -->
      <div v-else-if="modelType === 'llm'" class="max-h-[400px] space-y-3 overflow-y-auto pr-1">
        <div v-for="(models, pid) in groupByPlugin(llmModels)" :key="pid">
          <div class="mb-1 text-xs text-muted-foreground">{{ models[0]?.plugin_name }} ({{ pid }})</div>
          <RadioGroup v-model="selectedLlm" class="space-y-1 pl-2">
            <div
              v-for="model in models"
              :key="getModelKey(model)"
              class="flex items-center gap-2"
            >
              <RadioGroupItem :value="getModelKey(model)" />
              <Label :for="getModelKey(model)" class="cursor-pointer">
                {{ model.model_label || model.model_name }}
              </Label>
              <span class="text-xs text-muted-foreground">{{ model.model_name }}</span>
            </div>
          </RadioGroup>
        </div>
      </div>

      <!-- Embedding/Rerank 联动模式 -->
      <div v-else class="max-h-[500px] space-y-4 overflow-y-auto pr-1">
        <!-- Embedding 选择 -->
        <div>
          <div class="mb-2 font-medium">
            <Badge variant="outline">嵌入模型</Badge>
          </div>
          <RadioGroup v-model="selectedEmbedding" class="space-y-1 pl-2">
            <div v-for="(models, pid) in groupByPlugin(embeddingModels)" :key="pid">
              <div class="mb-1 text-xs text-muted-foreground">{{ models[0]?.plugin_name }}</div>
              <div
                v-for="model in models"
                :key="getModelKey(model)"
                class="flex items-center gap-2"
                :class="{ 'opacity-50 pointer-events-none': isEmbeddingDisabled(model) }"
              >
                <RadioGroupItem :value="getModelKey(model)" :disabled="isEmbeddingDisabled(model)" />
                <Label :class="{ 'cursor-pointer': !isEmbeddingDisabled(model) }">
                  {{ model.model_label || model.model_name }}
                </Label>
                <Badge v-if="isRecommended(model, selectedRerankItem)" variant="secondary" class="text-xs">
                  推荐
                </Badge>
              </div>
            </div>
          </RadioGroup>
        </div>

        <!-- 联动提示 -->
        <div
          v-if="selectedEmbedding && selectedRerank && selectedEmbeddingItem?.plugin_id !== selectedRerankItem?.plugin_id"
          class="rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-800"
        >
          embedding 和 rerank 默认模型必须来自同一插件
        </div>
        <div
          v-if="selectedEmbedding || selectedRerank"
          class="text-xs text-muted-foreground"
        >
          embedding 和 rerank 默认模型必须来自同一插件，选择一个后另一个列表会自动筛选
        </div>

        <!-- Rerank 选择 -->
        <div>
          <div class="mb-2 font-medium">
            <Badge variant="outline">排序模型</Badge>
          </div>
          <RadioGroup v-model="selectedRerank" class="space-y-1 pl-2">
            <div v-for="(models, pid) in groupByPlugin(rerankModels)" :key="pid">
              <div class="mb-1 text-xs text-muted-foreground">{{ models[0]?.plugin_name }}</div>
              <div
                v-for="model in models"
                :key="getModelKey(model)"
                class="flex items-center gap-2"
                :class="{ 'opacity-50 pointer-events-none': isRerankDisabled(model) }"
              >
                <RadioGroupItem :value="getModelKey(model)" :disabled="isRerankDisabled(model)" />
                <Label :class="{ 'cursor-pointer': !isRerankDisabled(model) }">
                  {{ model.model_label || model.model_name }}
                </Label>
                <Badge v-if="isRecommended(model, selectedEmbeddingItem)" variant="secondary" class="text-xs">
                  推荐
                </Badge>
              </div>
            </div>
          </RadioGroup>
        </div>
      </div>

      <DialogFooter class="gap-2 sm:gap-0">
        <Button variant="outline" @click="emit('update:open', false)">取消</Button>
        <Button :disabled="!canSubmit || saving || !!missingModelType" @click="handleSave">
          <Loader2 v-if="saving" class="mr-1 h-4 w-4 animate-spin" />
          确认
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
