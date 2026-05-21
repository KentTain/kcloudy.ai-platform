<script setup lang="ts">
/**
 * AppModal 对话框组件
 */
import { computed, watch } from "vue";

interface Props {
  modelValue: boolean;
  title?: string;
  size?: "sm" | "md" | "lg" | "xl";
  closable?: boolean;
  maskClosable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  size: "md",
  closable: true,
  maskClosable: true,
});

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  close: [];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const close = () => {
  visible.value = false;
  emit("close");
};

const handleMaskClick = () => {
  if (props.maskClosable) {
    close();
  }
};

// 禁止滚动
watch(visible, (val) => {
  document.body.style.overflow = val ? "hidden" : "";
});
</script>

<template>
  <Teleport to="body">
    <Transition name="app-modal">
      <div v-if="visible" class="app-modal__mask" @click.self="handleMaskClick">
        <div :class="['app-modal', `app-modal--${size}`]">
          <div v-if="title || $slots.header || closable" class="app-modal__header">
            <slot name="header">
              <h3 class="app-modal__title">{{ title }}</h3>
            </slot>
            <button v-if="closable" class="app-modal__close" @click="close">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
              </svg>
            </button>
          </div>
          <div class="app-modal__body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="app-modal__footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.app-modal__mask {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.app-modal {
  background-color: var(--color-surface-raised);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

/* 尺寸 */
.app-modal--sm {
  width: 400px;
}

.app-modal--md {
  width: 520px;
}

.app-modal--lg {
  width: 680px;
}

.app-modal--xl {
  width: 900px;
}

.app-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.app-modal__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.app-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.app-modal__close:hover {
  color: var(--color-text);
  background-color: var(--color-surface);
}

.app-modal__body {
  padding: 1.5rem;
  overflow-y: auto;
}

.app-modal__footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

/* 动画 */
.app-modal-enter-active,
.app-modal-leave-active {
  transition: opacity 0.2s ease;
}

.app-modal-enter-active .app-modal,
.app-modal-leave-active .app-modal {
  transition: transform 0.2s ease;
}

.app-modal-enter-from,
.app-modal-leave-to {
  opacity: 0;
}

.app-modal-enter-from .app-modal,
.app-modal-leave-to .app-modal {
  transform: scale(0.95);
}
</style>
