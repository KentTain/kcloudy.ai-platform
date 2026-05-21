import { defineStore } from "pinia";
import { ref } from "vue";

/**
 * 应用状态管理
 */
export const useAppStore = defineStore("app", () => {
  // 侧边栏状态
  const sidebarCollapsed = ref(false);

  // 设备类型
  const device = ref<"desktop" | "mobile">("desktop");

  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value;
  };

  // 设置侧边栏状态
  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed;
  };

  // 设置设备类型
  const setDevice = (type: "desktop" | "mobile") => {
    device.value = type;
    if (type === "mobile") {
      sidebarCollapsed.value = true;
    }
  };

  return {
    sidebarCollapsed,
    device,
    toggleSidebar,
    setSidebarCollapsed,
    setDevice,
  };
});

export default useAppStore;
