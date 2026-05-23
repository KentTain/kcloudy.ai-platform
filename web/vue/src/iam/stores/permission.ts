import { defineStore } from "pinia";
import { ref } from "vue";
import { getAllPermissions, getPermissions, getPermissionsByResource } from "../api/permission";
import type { Permission, PermissionGroup } from "../types";

export const usePermissionStore = defineStore("iam-permission", () => {
  const permissions = ref<Permission[]>([]);
  const permissionGroups = ref<PermissionGroup[]>([]);
  const loading = ref(false);
  const total = ref(0);

  const fetchPermissions = async (params?: { page?: number; page_size?: number; resource?: string }) => {
    loading.value = true;
    try {
      const response = await getPermissions(params);
      permissions.value = response.data.items;
      total.value = response.data.total;
    } finally {
      loading.value = false;
    }
  };

  const fetchAllPermissions = async () => {
    loading.value = true;
    try {
      const response = await getAllPermissions();
      permissions.value = response.data;
      total.value = response.data.length;
    } finally {
      loading.value = false;
    }
  };

  const fetchPermissionGroups = async () => {
    loading.value = true;
    try {
      const response = await getPermissionsByResource();
      permissionGroups.value = response.data;
    } finally {
      loading.value = false;
    }
  };

  return {
    permissions,
    permissionGroups,
    loading,
    total,
    fetchPermissions,
    fetchAllPermissions,
    fetchPermissionGroups,
  };
});
