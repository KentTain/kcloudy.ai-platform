import { ref, readonly } from "vue";

const isOpen = ref(false);

/**
 * 命令面板状态管理组合式函数
 * 用于在 AppNavbar 和 CommandPalette 组件之间共享状态
 */
export function useCommandPalette() {
  function openCommandPalette() {
    isOpen.value = true;
  }

  function closeCommandPalette() {
    isOpen.value = false;
  }

  function toggleCommandPalette() {
    isOpen.value = !isOpen.value;
  }

  return {
    /** 命令面板是否打开（只读） */
    isOpen: readonly(isOpen),
    /** 打开命令面板 */
    openCommandPalette,
    /** 关闭命令面板 */
    closeCommandPalette,
    /** 切换命令面板 */
    toggleCommandPalette,
  };
}
