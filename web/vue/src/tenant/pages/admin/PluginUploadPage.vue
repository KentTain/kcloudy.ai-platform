<script setup lang="ts">
import {
  Check,
  ChevronRight,
  Upload,
  Loader2,
  AlertCircle,
  CheckCircle,
  Package,
  X,
} from "@lucide/vue";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { Button, Checkbox } from "@/components";
import { notifySuccess } from "@/framework/utils/feedback";
import {
  parsePluginPackage,
  uploadPluginPackage,
} from "@/tenant/api/plugin";
import type { ParsedPluginInfo, UploadPluginResponse } from "@/tenant/api/plugin";

const router = useRouter();

// 步骤状态
const currentStep = ref(0);
const steps = [
  { title: "上传文件", description: "选择插件包" },
  { title: "预览确认", description: "确认插件信息" },
  { title: "注册结果", description: "查看注册状态" },
];

// 第一步：上传文件
const selectedFile = ref<File | null>(null);
const overwrite = ref(false);
const isDragging = ref(false);
const isParsing = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

// 第二步：预览确认
const parsedInfo = ref<ParsedPluginInfo | null>(null);

// 第三步：注册结果
const uploadResult = ref<UploadPluginResponse | null>(null);
const isUploading = ref(false);

// 错误提示
const errorMessage = ref("");
const showError = ref(false);

const showErrorMessage = (message: string) => {
  errorMessage.value = message;
  showError.value = true;
  // 5秒后自动关闭
  setTimeout(() => {
    showError.value = false;
  }, 5000);
};

const hideError = () => {
  showError.value = false;
};

// 计算属性：是否可以进入下一步
const canProceed = computed(() => {
  if (currentStep.value === 0) {
    return selectedFile.value !== null;
  }
  if (currentStep.value === 1) {
    // 如果插件已存在，需要勾选覆盖才能继续
    if (parsedInfo.value?.exists && !overwrite.value) {
      return false;
    }
    return parsedInfo.value !== null;
  }
  return false;
});

// 文件拖拽处理
const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragging.value = true;
};

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault();
  isDragging.value = false;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragging.value = false;

  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFileSelect(files[0]);
  }
};

// 文件选择处理
const handleFileSelect = (file: File) => {
  // 验证文件类型（.zip 或 .tar.gz）
  const validExtensions = [".zip", ".tar.gz", ".tgz"];
  const fileName = file.name.toLowerCase();
  const isValid = validExtensions.some((ext) => fileName.endsWith(ext));

  if (!isValid) {
    showErrorMessage("请上传 .zip 或 .tar.gz 格式的插件包");
    return;
  }

  selectedFile.value = file;
};

// 触发文件选择
const triggerFileSelect = () => {
  fileInputRef.value?.click();
};

const onFileInputChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    handleFileSelect(file);
  }
};

// 清除已选文件
const clearFile = () => {
  selectedFile.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
};

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
  return (bytes / (1024 * 1024)).toFixed(2) + " MB";
};

// 第一步：解析插件包
const handleParse = async () => {
  if (!selectedFile.value) return;

  isParsing.value = true;

  try {
    const response = await parsePluginPackage(selectedFile.value);

    if (response.data) {
      parsedInfo.value = response.data;
      currentStep.value = 1;
    }
  } catch (error: any) {
    console.error("解析插件包失败:", error);
    const message = error?.response?.data?.msg || error?.message || "解析失败";
    showErrorMessage(message);
  } finally {
    isParsing.value = false;
  }
};

// 返回第一步
const handleBack = () => {
  currentStep.value = 0;
  parsedInfo.value = null;
};

// 第二步：确认上传
const handleUpload = async () => {
  if (!selectedFile.value) return;

  // 如果插件已存在，需要确认覆盖
  if (parsedInfo.value?.exists && !overwrite.value) {
    showErrorMessage("插件已存在，请勾选覆盖选项");
    return;
  }

  isUploading.value = true;

  try {
    const response = await uploadPluginPackage(
      selectedFile.value,
      parsedInfo.value?.exists ? overwrite.value : undefined
    );

    if (response.data) {
      uploadResult.value = response.data;
      currentStep.value = 2;
      notifySuccess("插件注册成功");
    }
  } catch (error: any) {
    console.error("上传插件包失败:", error);
    const message = error?.response?.data?.msg || error?.message || "上传失败";
    showErrorMessage(message);
  } finally {
    isUploading.value = false;
  }
};

// 第三步：返回列表
const handleFinish = () => {
  router.push("/admin/plugin-definitions");
};

// 重新上传
const handleRetry = () => {
  currentStep.value = 0;
  selectedFile.value = null;
  parsedInfo.value = null;
  uploadResult.value = null;
  overwrite.value = false;
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col" data-testid="plugin-upload-page">
    <!-- 主布局容器 -->
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden border rounded-lg bg-card">
      <!-- 步骤栏 (Header) -->
      <div class="border-b bg-card px-6 py-4">
        <div class="flex items-center justify-center gap-2">
          <template v-for="(step, index) in steps" :key="index">
            <div
              class="flex items-center gap-2 rounded-full px-4 py-2 transition-colors"
              :class="[
                currentStep === index
                  ? 'bg-primary text-primary-foreground'
                  : currentStep > index
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted text-muted-foreground',
              ]"
            >
              <div
                class="flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold"
                :class="[
                  currentStep === index
                    ? 'bg-primary-foreground/20'
                    : currentStep > index
                      ? 'bg-primary/20'
                      : 'bg-muted-foreground/20',
                ]"
              >
                <Check v-if="currentStep > index" class="h-4 w-4" />
                <span v-else>{{ index + 1 }}</span>
              </div>
              <div class="text-sm font-medium">{{ step.title }}</div>
            </div>
            <ChevronRight
              v-if="index < steps.length - 1"
              class="text-muted-foreground h-4 w-4"
            />
          </template>
        </div>
      </div>

      <!-- 表单栏 (Content) - 居中，可滚动 -->
      <div class="min-h-0 flex-1 overflow-auto">
        <div class="flex h-full items-start justify-center p-8">
          <!-- 第一步：上传文件 -->
          <div v-if="currentStep === 0" class="w-full max-w-lg space-y-6">
            <!-- 拖拽上传区域 -->
            <div
              class="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer"
              :class="[
                isDragging
                  ? 'border-primary bg-primary/5'
                  : selectedFile
                    ? 'border-green-500 bg-green-50'
                    : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50',
              ]"
              @dragover="handleDragOver"
              @dragleave="handleDragLeave"
              @drop="handleDrop"
              @click="triggerFileSelect"
            >
              <input
                ref="fileInputRef"
                type="file"
                accept=".zip,.tar.gz,.tgz"
                class="hidden"
                data-testid="file-input"
                @change="onFileInputChange"
              />

              <template v-if="selectedFile">
                <Package class="h-12 w-12 text-green-500" />
                <div class="mt-4 text-center">
                  <div class="font-medium">{{ selectedFile.name }}</div>
                  <div class="text-muted-foreground mt-1 text-xs">
                    {{ formatFileSize(selectedFile.size) }}
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  class="mt-4"
                  @click.stop="clearFile"
                >
                  移除文件
                </Button>
              </template>

              <template v-else>
                <Upload class="text-muted-foreground h-12 w-12" />
                <div class="mt-4 text-center">
                  <div class="font-medium">拖拽文件到此处或点击选择</div>
                  <div class="text-muted-foreground mt-1 text-xs">
                    支持 .zip 或 .tar.gz 格式
                  </div>
                </div>
              </template>
            </div>

            <!-- 覆盖已存在复选框 -->
            <div class="flex items-center gap-2">
              <Checkbox
                :checked="overwrite"
                data-testid="overwrite-checkbox"
                @update:checked="overwrite = $event"
              />
              <label class="text-sm cursor-pointer">覆盖已存在的插件</label>
            </div>
          </div>

          <!-- 第二步：预览确认 -->
          <div v-if="currentStep === 1 && parsedInfo" class="w-full max-w-lg space-y-4">
            <!-- 已存在提示 -->
            <div
              v-if="parsedInfo.exists"
              class="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4"
            >
              <AlertCircle class="h-5 w-5 flex-shrink-0 text-amber-500" />
              <div>
                <div class="font-medium text-amber-800">插件已存在</div>
                <div class="mt-1 text-sm text-amber-700">
                  该插件已在系统中注册。如需更新，请勾选"覆盖已存在的插件"选项。
                </div>
              </div>
            </div>

            <!-- 插件信息 -->
            <div class="space-y-3 rounded-lg border p-4">
              <div class="flex items-center justify-between border-b pb-3">
                <span class="text-muted-foreground text-sm">插件 ID</span>
                <span class="font-medium">{{ parsedInfo.plugin_id }}</span>
              </div>
              <div class="flex items-center justify-between border-b pb-3">
                <span class="text-muted-foreground text-sm">版本</span>
                <span class="font-medium">v{{ parsedInfo.version }}</span>
              </div>
              <div class="flex items-center justify-between border-b pb-3">
                <span class="text-muted-foreground text-sm">名称</span>
                <span class="font-medium">{{ parsedInfo.name }}</span>
              </div>
              <div class="flex items-center justify-between border-b pb-3">
                <span class="text-muted-foreground text-sm">类型</span>
                <span class="font-medium">{{ parsedInfo.manifest_type }}</span>
              </div>
              <div>
                <span class="text-muted-foreground text-sm">描述</span>
                <p class="mt-1 text-sm">{{ parsedInfo.description || "--" }}</p>
              </div>
            </div>

            <!-- 覆盖选项（已存在时显示） -->
            <div
              v-if="parsedInfo.exists"
              class="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-4"
            >
              <Checkbox
                :checked="overwrite"
                data-testid="confirm-overwrite-checkbox"
                @update:checked="overwrite = $event"
              />
              <label class="text-sm text-amber-800 cursor-pointer">
                确认覆盖已存在的插件
              </label>
            </div>
          </div>

          <!-- 第三步：注册结果 -->
          <div v-if="currentStep === 2 && uploadResult" class="w-full max-w-lg space-y-4">
            <!-- 成功图标 -->
            <div class="flex flex-col items-center py-8">
              <div class="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <CheckCircle class="h-8 w-8 text-green-600" />
              </div>
              <div class="mt-4 text-lg font-semibold">注册成功</div>
              <div class="text-muted-foreground mt-1 text-sm">
                {{ uploadResult.message }}
              </div>
            </div>

            <!-- 插件信息 -->
            <div class="space-y-3 rounded-lg border p-4">
              <div class="flex items-center justify-between border-b pb-3">
                <span class="text-muted-foreground text-sm">插件 ID</span>
                <span class="font-medium">{{ uploadResult.plugin_id }}</span>
              </div>
              <div class="flex items-center justify-between border-b pb-3">
                <span class="text-muted-foreground text-sm">版本</span>
                <span class="font-medium">v{{ uploadResult.version }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-muted-foreground text-sm">唯一标识</span>
                <span class="font-medium text-xs">{{ uploadResult.plugin_unique_identifier }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮栏 (Footer) - 底部悬浮透明 -->
      <div class="border-t bg-card/80 backdrop-blur-sm px-6 py-4">
        <div class="flex items-center justify-center gap-3">
          <!-- 第一步按钮 -->
          <template v-if="currentStep === 0">
            <Button variant="outline" @click="router.push('/admin/plugin-definitions')">
              取消
            </Button>
            <Button
              :disabled="!selectedFile || isParsing"
              data-testid="parse-btn"
              @click="handleParse"
            >
              <Loader2 v-if="isParsing" class="mr-2 h-4 w-4 animate-spin" />
              <Check v-else class="mr-2 h-4 w-4" />
              {{ isParsing ? "解析中..." : "下一步" }}
            </Button>
          </template>

          <!-- 第二步按钮 -->
          <template v-if="currentStep === 1">
            <Button variant="outline" data-testid="back-btn" @click="handleBack">
              上一步
            </Button>
            <Button variant="outline" @click="router.push('/admin/plugin-definitions')">
              取消
            </Button>
            <Button
              :disabled="!canProceed || isUploading"
              data-testid="upload-btn"
              @click="handleUpload"
            >
              <Loader2 v-if="isUploading" class="mr-2 h-4 w-4 animate-spin" />
              <Check v-else class="mr-2 h-4 w-4" />
              {{ isUploading ? "注册中..." : "确认注册" }}
            </Button>
          </template>

          <!-- 第三步按钮 -->
          <template v-if="currentStep === 2">
            <Button variant="outline" data-testid="retry-btn" @click="handleRetry">
              继续上传
            </Button>
            <Button data-testid="finish-btn" @click="handleFinish">
              返回列表
            </Button>
          </template>
        </div>
      </div>
    </div>

    <!-- 错误提示 - 左下角 -->
    <Transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <div
        v-if="showError"
        class="fixed bottom-4 left-4 z-50 flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 shadow-lg"
        data-testid="error-message"
      >
        <AlertCircle class="h-5 w-5 text-red-600 flex-shrink-0" />
        <span class="text-sm text-red-800">{{ errorMessage }}</span>
        <button
          class="ml-2 text-red-600 hover:text-red-800"
          @click="hideError"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
    </Transition>
  </div>
</template>
