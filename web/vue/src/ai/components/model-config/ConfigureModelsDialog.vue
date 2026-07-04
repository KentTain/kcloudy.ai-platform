<script setup lang="ts">
/**
 * 模型配置 - 配置模型弹窗
 *
 * 多选弹窗，选择该插件下要启用哪些模型。
 */
import { ref, watch } from "vue";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-vue-next";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import { getAvailableModels, setEnabledModels } from "@/ai/api/modelConfig";
import type { AvailableModelItem, ModelTypeKey } from "@/ai/types/modelConfig";
import { MODEL_TYPE_LABELS } from "@/ai/types/modelConfig";

const props = defineProps<{
  open: boolean;
  pluginId: string;
  pluginName: string;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
  (e: "saved"): void;
}>();

const loading = ref(false);
const saving = ref(false);
const models = ref<AvailableModelItem[]>([]);
const selectedModelNames = ref<Set<string>>(new Set());

// 按 model_type 分组
const groupedModels = ref<Record<string, AvailableModelItem[]>>({});

const hasEmbedding = ref(false);
const hasRerank = ref(false);

async function loadModels() {
  loading.value = true;
  try {
    const data = await getAvailableModels(props.pluginId);
    models.value = data;

    // 分组
    const grouped: Record<string, AvailableModelItem[]> = {};
    for (const m of data) {
      if (!grouped[m.model_type]) grouped[m.model_type] = [];
      grouped[m.model_type].push(m);
    }
    groupedModels.value = grouped;

    // 默认选中已启用的
    const enabled = new Set(data.filter((m) => m.is_enabled).map((m) => m.model_name));
    selectedModelNames.value = enabled;

    // 检查 embedding/rerank
    hasEmbedding.value = data.some((m) => m.model_type === "text-embedding");
    hasRerank.value = data.some((m) => m.model_type === "rerank");
  } catch {
    notifyError("获取模型列表失败");
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.open,
  (val) => {
    if (val) loadModels();
  },
);

function toggleModel(name: string) {
  const s = new Set(selectedModelNames.value);
  if (s.has(name)) {
    s.delete(name);
  } else {
    s.add(name);
  }
  selectedModelNames.value = s;
}

async function handleSave() {
  saving.value = true;
  try {
    await setEnabledModels(props.pluginId, {
      model_names: Array.from(selectedModelNames.value),
    });
    notifySuccess("模型配置已保存");
    emit("update:open", false);
    emit("saved");
  } catch {
    notifyError("保存失败");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[520px]">
      <DialogHeader>
        <DialogTitle>配置模型 - {{ pluginName }}</DialogTitle>
        <DialogDescription>选择该插件下要启用的模型</DialogDescription>
      </DialogHeader>

      <!-- Embedding/Rerank 提示 -->
      <div
        v-if="hasEmbedding && !hasRerank"
        class="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
      >
        建议同时配置排序（rerank）模型，嵌入和排序模型需来自同一插件
      </div>
      <div
        v-if="hasRerank && !hasEmbedding"
        class="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
      >
        建议同时配置嵌入（embedding）模型，嵌入和排序模型需来自同一插件
      </div>

      <div v-if="loading" class="flex items-center justify-center py-8">
        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
      </div>

      <div v-else class="max-h-[400px] space-y-4 overflow-y-auto pr-1">
        <div v-for="(items, type) in groupedModels" :key="type">
          <div class="mb-2">
            <Badge variant="outline">{{ MODEL_TYPE_LABELS[type as ModelTypeKey] || type }}</Badge>
          </div>
          <div class="space-y-2 pl-2">
            <div
              v-for="model in items"
              :key="model.model_name"
              class="flex items-center gap-2"
            >
              <Checkbox
                :id="model.model_name"
                :checked="selectedModelNames.has(model.model_name)"
                @update:checked="toggleModel(model.model_name)"
              />
              <Label :for="model.model_name" class="cursor-pointer">
                {{ model.model_label || model.model_name }}
              </Label>
              <span class="text-xs text-muted-foreground">{{ model.model_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter class="gap-2 sm:gap-0">
        <Button variant="outline" @click="emit('update:open', false)">取消</Button>
        <Button :disabled="saving" @click="handleSave">
          <Loader2 v-if="saving" class="mr-1 h-4 w-4 animate-spin" />
          保存
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
