import { defineStore } from "pinia";
import { computed } from "vue";

/**
 * 应用状态管理
 * 注：侧边栏状态由 shadcn Sidebar 组件内部管理
 */
export const useAppStore = defineStore("app", () => {
  // 设备类型（只读 computed，基于 window.innerWidth）
  const device = computed<"desktop" | "mobile">(() => {
    if (typeof window === "undefined") return "desktop";
    return window.innerWidth < 768 ? "mobile" : "desktop";
  });

  return {
    device,
  };
});

export default useAppStore;
