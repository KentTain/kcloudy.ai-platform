<template>
  <Dialog v-model:open="dialogVisible">
    <DialogContent :class="contentClass" :show-close-button="showCloseButton" z-index="10000">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2 text-base">
          <component :is="iconComponent" v-if="showIcon && iconComponent" :class="iconClass" />
          <span>{{ currentTitle }}</span>
        </DialogTitle>
      </DialogHeader>
      <div class="py-2">
        <slot>
          <p class="text-sm text-gray-700" v-html="currentContent"></p>
        </slot>
      </div>
      <DialogFooter class="gap-3">
        <DialogClose as-child v-if="currentShowCancel">
          <Button variant="outline" class="h-9" type="button" :disabled="loading" @click="handleCancel">
            {{ currentCancelText }}
          </Button>
        </DialogClose>
        <Button class="h-9" :disabled="loading" @click="handleConfirm">
          <Loader v-if="loading" class="size-4 animate-spin mr-2" />
          {{ currentConfirmText }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { AlertTriangle, CheckCircle, Info, Loader, XCircle } from "@lucide/vue";
import { computed, ref, watch } from "vue";

import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

/**
 * MessageBox 类型定义
 */
export type MessageBoxType = "success" | "warning" | "error" | "info";

/**
 * MessageBox 动作类型
 */
export type MessageBoxAction = "confirm" | "cancel";

/**
 * beforeClose 回调函数类型
 * 类似 ElMessageBox 的 beforeClose
 * @param action - 用户执行的动作
 * @param done - 关闭对话框的回调函数
 */
export type BeforeCloseCallback = (action: MessageBoxAction, done: () => void) => void;

/**
 * MessageBox 选项接口
 */
export interface MessageBoxOptions {
  /** 关闭前的回调函数（类似 ElMessageBox.beforeClose） */
  beforeClose?: BeforeCloseCallback;
  /** 取消按钮文本 */
  cancelText?: string;
  /** 确认按钮文本 */
  confirmText?: string;
  /** 内容（支持 HTML） */
  content?: string;
  /** 内容区样式类 */
  contentClass?: string;
  /** 自定义图标组件 */
  customIcon?: object;
  /** 是否显示取消按钮 */
  showCancel?: boolean;
  /** 是否显示右上角关闭按钮 */
  showCloseButton?: boolean;
  /** 是否显示图标 */
  showIcon?: boolean;
  /** 标题 */
  title?: string;
  /** 类型：success | warning | error | info */
  type?: MessageBoxType;
}

/**
 * 组件属性
 */
interface Props {
  /** 关闭前的回调函数 */
  beforeClose?: BeforeCloseCallback;
  /** 取消按钮文本 */
  cancelText?: string;
  /** 确认按钮文本 */
  confirmText?: string;
  /** 内容（支持 HTML） */
  content?: string;
  /** 内容区样式类 */
  contentClass?: string;
  /** 自定义图标组件 */
  customIcon?: object;
  /** 是否显示取消按钮 */
  showCancel?: boolean;
  /** 是否显示右上角关闭按钮 */
  showCloseButton?: boolean;
  /** 是否显示图标 */
  showIcon?: boolean;
  /** 标题 */
  title?: string;
  /** 类型：success | warning | error | info */
  type?: MessageBoxType;
}

const props = withDefaults(defineProps<Props>(), {
  cancelText: "取消",
  confirmText: "确认",
  content: "",
  contentClass: "sm:max-w-[420px]",
  showCancel: true,
  showCloseButton: true,
  showIcon: true,
  title: "提示",
  type: "info",
});

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: "confirm", done: () => void): void;
  (e: "cancel", done: () => void): void;
  (e: "close"): void;
}>();

// 对话框显示状态
const dialogVisible = ref(false);
// 加载状态
const loading = ref(false);
// 保存当前的 beforeClose 回调
const currentBeforeClose = ref<BeforeCloseCallback | undefined>(undefined);
// 动态选项（用于 open() 方法传入的值）
const dynamicOptions = ref<Partial<MessageBoxOptions>>({});

// 当前使用的值（优先使用 dynamicOptions，回退到 props）
const currentTitle = computed(() => dynamicOptions.value.title ?? props.title);
const currentContent = computed(() => dynamicOptions.value.content ?? props.content);
const currentType = computed(() => dynamicOptions.value.type ?? props.type);
const currentConfirmText = computed(() => dynamicOptions.value.confirmText ?? props.confirmText);
const currentCancelText = computed(() => dynamicOptions.value.cancelText ?? props.cancelText);
const currentShowCancel = computed(() => dynamicOptions.value.showCancel ?? props.showCancel);
const currentShowIcon = computed(() => dynamicOptions.value.showIcon ?? props.showIcon);
const currentShowCloseButton = computed(() => dynamicOptions.value.showCloseButton ?? props.showCloseButton);
const currentContentClass = computed(() => dynamicOptions.value.contentClass ?? props.contentClass);
const currentCustomIcon = computed(() => dynamicOptions.value.customIcon ?? props.customIcon);

// 图标组件映射
const iconMap: Record<MessageBoxType, object> = {
  error: XCircle,
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
};

// 图标颜色映射
const iconColorMap: Record<MessageBoxType, string> = {
  error: "text-red-500",
  info: "text-blue-500",
  success: "text-green-500",
  warning: "text-amber-500",
};

/**
 * 图标组件
 */
const iconComponent = computed(() => {
  return currentCustomIcon.value || iconMap[currentType.value];
});

/**
 * 图标样式类
 */
const iconClass = computed(() => {
  return `size-5 ${iconColorMap[currentType.value]}`;
});

/**
 * 打开对话框
 * @param options - 对话框选项
 */
function open(options?: MessageBoxOptions) {
  if (options) {
    // 保存动态选项
    dynamicOptions.value = { ...options };
    currentBeforeClose.value = options.beforeClose;
  } else {
    // 清空动态选项，使用 props
    dynamicOptions.value = {};
    currentBeforeClose.value = props.beforeClose;
  }
  dialogVisible.value = true;
  loading.value = false;
}

/**
 * 关闭对话框
 */
function close() {
  dialogVisible.value = false;
  loading.value = false;
  emit("close");
}

/**
 * 执行关闭前的回调
 * @param action - 用户执行的动作
 */
function executeBeforeClose(action: MessageBoxAction) {
  const done = () => {
    loading.value = false;
    close();
  };

  // 如果有 beforeClose 回调，执行它
  if (currentBeforeClose.value) {
    loading.value = action === "confirm"; // 确认操作时显示加载状态
    currentBeforeClose.value(action, done);
  } else {
    // 没有回调，发射事件并直接关闭
    if (action === "confirm") {
      emit("confirm", done);
    } else {
      emit("cancel", done);
    }
    // 如果事件处理器没有调用 done，则自动关闭
    done();
  }
}

/**
 * 处理确认按钮点击
 */
function handleConfirm() {
  if (loading.value) return;
  executeBeforeClose("confirm");
}

/**
 * 处理取消按钮点击
 */
function handleCancel() {
  if (loading.value) return;
  executeBeforeClose("cancel");
}

/**
 * 监听对话框关闭，清空动态选项
 */
watch(dialogVisible, (val) => {
  if (!val) {
    loading.value = false;
    // 延迟清空，避免动画期间出现问题
    setTimeout(() => {
      dynamicOptions.value = {};
    }, 200);
  }
});

// 暴露方法给父组件
defineExpose({
  close,
  open,
});
</script>

<style scoped>
/* 遮罩层动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
