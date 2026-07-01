import { defineStore } from "pinia";
import { ref } from "vue";
import { getMenus } from "../api/menu";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import type { MenuTreeNode } from "../types";

export const useMenuStore = defineStore("iam-menu", () => {
  const menus = ref<MenuTreeNode[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchMenus = async () => {
    loading.value = true;
    error.value = null;
    try {
      const response = await getMenus();
      menus.value = response.data.menus;
    } catch (err: any) {
      error.value = getErrorMessage(err, "获取菜单失败");
      notifyError(error.value);
    } finally {
      loading.value = false;
    }
  };

  return {
    menus,
    loading,
    error,
    fetchMenus,
  };
});
