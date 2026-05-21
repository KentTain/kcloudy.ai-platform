<script setup lang="ts">
/**
 * AppSelect 下拉选择组件
 */
import { computed, ref, onMounted, onUnmounted } from "vue";

interface Option {
  label: string;
  value: string | number;
  disabled?: boolean;
}

interface Props {
  modelValue?: string | number | null;
  options: Option[];
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  size?: "sm" | "md" | "lg";
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: "请选择",
  size: "md",
  clearable: false,
  disabled: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string | number | null];
  change: [value: string | number | null];
}>();

const dropdownRef = ref<HTMLElement>();
const isOpen = ref(false);

const selectedOption = computed(() =>
  props.options.find((opt) => opt.value === props.modelValue)
);

const selectClasses = computed(() => [
  "app-select",
  `app-select--${props.size}`,
  {
    "app-select--open": isOpen.value,
    "app-select--disabled": props.disabled,
  },
]);

const toggleDropdown = () => {
  if (!props.disabled) {
    isOpen.value = !isOpen.value;
  }
};

const selectOption = (option: Option) => {
  if (!option.disabled) {
    emit("update:modelValue", option.value);
    emit("change", option.value);
    isOpen.value = false;
  }
};

const clearValue = (event: MouseEvent) => {
  event.stopPropagation();
  emit("update:modelValue", null);
  emit("change", null);
};

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<template>
  <div ref="dropdownRef" :class="selectClasses">
    <div class="app-select__trigger" @click="toggleDropdown">
      <span v-if="selectedOption" class="app-select__value">
        {{ selectedOption.label }}
      </span>
      <span v-else class="app-select__placeholder">{{ placeholder }}</span>
      <span v-if="clearable && modelValue !== null" class="app-select__clear" @click="clearValue">
        <svg viewBox="0 0 24 24" width="14" height="14">
          <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
        </svg>
      </span>
      <span class="app-select__arrow">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M7 10l5 5 5-5z" />
        </svg>
      </span>
    </div>
    <Transition name="app-select-dropdown">
      <div v-if="isOpen" class="app-select__dropdown">
        <div
          v-for="option in options"
          :key="option.value"
          :class="[
            'app-select__option',
            {
              'app-select__option--selected': option.value === modelValue,
              'app-select__option--disabled': option.disabled,
            },
          ]"
          @click="selectOption(option)"
        >
          {{ option.label }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.app-select {
  position: relative;
  display: inline-block;
  width: 100%;
}

.app-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-ui);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.app-select--sm .app-select__trigger {
  padding: 0.375rem 0.5rem;
  font-size: 0.875rem;
}

.app-select--lg .app-select__trigger {
  padding: 0.75rem 1rem;
  font-size: 1rem;
}

.app-select__trigger:hover {
  border-color: var(--color-primary);
}

.app-select--open .app-select__trigger {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-border-primary);
}

.app-select--disabled .app-select__trigger {
  background-color: var(--color-surface);
  cursor: not-allowed;
}

.app-select__value {
  flex: 1;
  color: var(--color-text);
}

.app-select__placeholder {
  flex: 1;
  color: var(--color-text-disabled);
}

.app-select__clear {
  display: flex;
  align-items: center;
  color: var(--color-text-muted);
  transition: color var(--transition-fast);
}

.app-select__clear:hover {
  color: var(--color-text);
}

.app-select__arrow {
  display: flex;
  align-items: center;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.app-select--open .app-select__arrow {
  transform: rotate(180deg);
}

.app-select__dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background-color: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-ui);
  box-shadow: var(--shadow-lg);
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
}

.app-select__option {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.app-select__option:hover {
  background-color: var(--color-primary-subtle);
}

.app-select__option--selected {
  color: var(--color-primary);
  font-weight: 600;
}

.app-select__option--disabled {
  color: var(--color-text-disabled);
  cursor: not-allowed;
}

.app-select__option--disabled:hover {
  background-color: transparent;
}

/* 动画 */
.app-select-dropdown-enter-active,
.app-select-dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.app-select-dropdown-enter-from,
.app-select-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
