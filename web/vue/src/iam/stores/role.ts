import { defineStore } from "pinia";
import { ref } from "vue";
import {
  assignRolePermissions,
  createRole,
  deleteRole,
  getRole,
  getRolePermissions,
  getRoles,
  updateRole,
} from "../api/role";
import { getErrorMessage, notifyError, notifySuccess } from "../utils/feedback";
import type { CreateRoleParams, Permission, Role, UpdateRoleParams } from "../types";

export const useRoleStore = defineStore("iam-role", () => {
  const roles = ref<Role[]>([]);
  const currentRole = ref<Role | null>(null);
  const currentRolePermissions = ref<Permission[]>([]);
  const loading = ref(false);
  const total = ref(0);

  const fetchRoles = async (params?: { page?: number; page_size?: number; keyword?: string }) => {
    loading.value = true;
    try {
      const response = await getRoles(params);
      roles.value = response.data.items;
      total.value = response.data.total;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取角色列表失败"));
      console.error("fetchRoles error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchRole = async (id: string) => {
    loading.value = true;
    try {
      const response = await getRole(id);
      currentRole.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取角色详情失败"));
      console.error("fetchRole error:", error);
    } finally {
      loading.value = false;
    }
  };

  const addRole = async (data: CreateRoleParams) => {
    loading.value = true;
    try {
      const response = await createRole(data);
      roles.value.unshift(response.data);
      total.value++;
      notifySuccess("创建角色成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "创建角色失败"));
      console.error("addRole error:", error);
    } finally {
      loading.value = false;
    }
  };

  const editRole = async (id: string, data: UpdateRoleParams) => {
    loading.value = true;
    try {
      const response = await updateRole(id, data);
      const index = roles.value.findIndex((r) => r.id === id);
      if (index !== -1) {
        roles.value[index] = response.data;
      }
      notifySuccess("更新角色成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "更新角色失败"));
      console.error("editRole error:", error);
    } finally {
      loading.value = false;
    }
  };

  const removeRole = async (id: string) => {
    loading.value = true;
    try {
      await deleteRole(id);
      roles.value = roles.value.filter((r) => r.id !== id);
      total.value--;
      notifySuccess("删除角色成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "删除角色失败"));
      console.error("removeRole error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchRolePermissions = async (role_id: string) => {
    loading.value = true;
    try {
      const response = await getRolePermissions(role_id);
      currentRolePermissions.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取角色权限失败"));
      console.error("fetchRolePermissions error:", error);
    } finally {
      loading.value = false;
    }
  };

  const updateRolePermissions = async (role_id: string, permission_ids: string[]) => {
    loading.value = true;
    try {
      await assignRolePermissions(role_id, { permission_ids });
      await fetchRolePermissions(role_id);
      notifySuccess("更新角色权限成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "更新角色权限失败"));
      console.error("updateRolePermissions error:", error);
    } finally {
      loading.value = false;
    }
  };

  return {
    roles,
    currentRole,
    currentRolePermissions,
    loading,
    total,
    fetchRoles,
    fetchRole,
    addRole,
    editRole,
    removeRole,
    fetchRolePermissions,
    updateRolePermissions,
  };
});
