import { defineStore } from "pinia";
import { ref } from "vue";
import { getMenus } from "../api/menu";
import type { MenuTreeNode } from "../types";

export const useMenuStore = defineStore("iam-menu", () => {
  const menus = ref<MenuTreeNode[]>([]);
  const loading = ref(false);

  const fetchMenus = async () => {
    loading.value = true;
    try {
      const response = await getMenus();
      menus.value = response.data.menus;
    } finally {
      loading.value = false;
    }
  };

  return {
    menus,
    loading,
    fetchMenus,
  };
});
