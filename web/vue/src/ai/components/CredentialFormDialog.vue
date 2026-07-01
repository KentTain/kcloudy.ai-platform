<script setup lang="ts">
/**
 * 凭证编辑弹窗
 *
 * 根据插件的 credentials-schema 动态生成表单字段，
 * 支持新增/编辑凭证和测试连通性。
 */
import { ref, watch, onMounted } from "vue";
import { Button } from "@/components";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  Input,
  Label,
  Switch,
} from "@/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw, Plug } from "lucide-vue-next";
import { notifySuccess, notifyError } from "@/framework/utils/feedback";
import {
  getPluginCredentialsSchema,
  createPluginCredential,
  updatePluginCredential,
  validatePluginCredential,
  type PluginCredentialsSchemaField,
  type PluginCredential,
} from "@/ai/api/plugin";

const props = defineProps<{
  open: boolean;
  pluginId: string;
  mode: "create" | "edit";
  credential?: PluginCredential | null;
}>();

const emit = defineEmits<{
  "update:open": [value: boolean];
  saved: [];
}>();

const schema = ref<PluginCredentialsSchemaField[]>([]);
const formValues = ref<Record<string, any>>({});
const credentialName = ref("");
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);

// 加载凭证架构
const loadSchema = async () => {
  loading.value = true;
  try {
    const response = await getPluginCredentialsSchema(props.pluginId);
    if (response.data) {
      schema.value = response.data;
      // 初始化表单默认值
      const defaults: Record<string, any> = {};
      for (const field of schema.value) {
        if (field.default !== undefined && field.default !== null) {
          defaults[field.name] = field.default;
        } else if (field.type === "boolean") {
          defaults[field.name] = false;
        } else {
          defaults[field.name] = "";
        }
      }
      formValues.value = defaults;
    }
  } catch (error: any) {
    notifyError("加载凭证架构失败");
  } finally {
    loading.value = false;
  }
};

// 编辑模式下填充已有值
watch(
  () => props.open,
  (val) => {
    if (val) {
      loadSchema();
      if (props.mode === "edit" && props.credential) {
        credentialName.value = props.credential.name;
        if (props.credential.credentials) {
          formValues.value = { ...formValues.value, ...props.credential.credentials };
        }
      } else {
        credentialName.value = "";
      }
    }
  }
);

// 更新字段值
const updateField = (name: string, value: any) => {
  formValues.value = { ...formValues.value, [name]: value };
};

// 验证必填字段
const validate = (): string | null => {
  if (!credentialName.value.trim()) {
    return "请输入凭证名称";
  }
  for (const field of schema.value) {
    if (field.required && !formValues.value[field.name]) {
      return `请填写 ${field.label || field.name}`;
    }
  }
  return null;
};

// 测试连通性
const handleTest = async () => {
  testing.value = true;
  try {
    const response = await validatePluginCredential(props.pluginId, {
      credentials: formValues.value,
    });
    if (response.data?.success) {
      notifySuccess("凭证验证通过");
    } else {
      notifyError(`凭证验证失败: ${response.data?.error || "未知错误"}`);
    }
  } catch (error: any) {
    notifyError(`凭证验证失败: ${error?.message || "未知错误"}`);
  } finally {
    testing.value = false;
  }
};

// 保存凭证
const handleSave = async () => {
  const error = validate();
  if (error) {
    notifyError(error);
    return;
  }

  saving.value = true;
  try {
    if (props.mode === "create") {
      await createPluginCredential(props.pluginId, {
        name: credentialName.value,
        credentials: formValues.value,
      });
      notifySuccess("凭证创建成功");
    } else if (props.credential) {
      await updatePluginCredential(
        props.pluginId,
        props.credential.id,
        {
          name: credentialName.value,
          credentials: formValues.value,
        }
      );
      notifySuccess("凭证更新成功");
    }
    emit("saved");
    emit("update:open", false);
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "保存凭证失败");
  } finally {
    saving.value = false;
  }
};
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[520px]">
      <DialogHeader>
        <DialogTitle>{{ mode === "create" ? "新增凭证" : "编辑凭证" }}</DialogTitle>
        <DialogDescription>
          配置插件访问凭证，配置完成后可点击"测试连通性"验证
        </DialogDescription>
      </DialogHeader>

      <div v-if="loading" class="py-8 text-center text-muted-foreground">
        加载中...
      </div>

      <div v-else-if="schema.length === 0" class="py-8 text-center text-muted-foreground">
        该插件无需配置凭证
      </div>

      <form v-else class="flex flex-col gap-4" @submit.prevent="handleSave">
        <!-- 凭证名称 -->
        <div class="space-y-2">
          <Label>凭证名称 <span class="text-destructive">*</span></Label>
          <Input
            v-model="credentialName"
            placeholder="例如：默认凭证"
          />
        </div>

        <!-- 动态字段 -->
        <div v-for="field in schema" :key="field.name" class="space-y-1.5">
          <Label>
            {{ field.label || field.name }}
            <span v-if="field.required" class="text-destructive">*</span>
          </Label>

          <!-- secret-input -->
          <Input
            v-if="field.type === 'secret-input'"
            type="password"
            :placeholder="field.placeholder || `请输入${field.label || field.name}`"
            :model-value="formValues[field.name]"
            @update:model-value="updateField(field.name, $event)"
          />

          <!-- text-input -->
          <Input
            v-else-if="field.type === 'text-input' || !field.type"
            :placeholder="field.placeholder || `请输入${field.label || field.name}`"
            :model-value="formValues[field.name]"
            @update:model-value="updateField(field.name, $event)"
          />

          <!-- select -->
          <Select
            v-else-if="field.type === 'select'"
            :model-value="formValues[field.name]"
            @update:model-value="updateField(field.name, $event)"
          >
            <SelectTrigger>
              <SelectValue :placeholder="field.placeholder || '请选择'" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="option in field.options"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label || option.value }}
              </SelectItem>
            </SelectContent>
          </Select>

          <!-- number -->
          <Input
            v-else-if="field.type === 'number'"
            type="number"
            :placeholder="field.placeholder || `请输入${field.label || field.name}`"
            :model-value="formValues[field.name]"
            @update:model-value="updateField(field.name, $event ? Number($event) : $event)"
          />

          <!-- boolean -->
          <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
            <Switch
              :checked="!!formValues[field.name]"
              @update:checked="updateField(field.name, $event)"
            />
          </div>

          <!-- 描述/帮助 -->
          <p v-if="field.description" class="text-muted-foreground text-xs">
            {{ field.description }}
          </p>
          <p v-if="field.help" class="text-muted-foreground text-xs">
            {{ field.help }}
            <a
              v-if="field.url"
              :href="field.url"
              target="_blank"
              class="text-primary underline"
            >
              查看详情
            </a>
          </p>
        </div>
      </form>

      <DialogFooter class="gap-2 sm:gap-0">
        <Button
          variant="outline"
          :disabled="saving || testing || schema.length === 0"
          @click="handleTest"
        >
          <RefreshCw v-if="testing" class="mr-1 h-3.5 w-3.5 animate-spin" />
          <Plug v-else class="mr-1 h-3.5 w-3.5" />
          {{ testing ? "测试中..." : "测试连通性" }}
        </Button>
        <Button variant="outline" @click="emit('update:open', false)">取消</Button>
        <Button
          :disabled="saving || schema.length === 0"
          @click="handleSave"
        >
          <RefreshCw v-if="saving" class="mr-1 h-3.5 w-3.5 animate-spin" />
          {{ saving ? "保存中..." : "保存" }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
