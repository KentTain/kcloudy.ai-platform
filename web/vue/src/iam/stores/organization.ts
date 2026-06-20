import { defineStore } from "pinia";
import { ref } from "vue";
import {
  createOrganization,
  deleteOrganization,
  getOrganization,
  getOrganizationTree,
  getOrganizationUsers,
  getOrganizations,
  setOrganizationLeader,
  updateOrganization,
} from "../api/organization";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { OrganizationCreate, Organization, OrganizationUser, OrganizationUpdate } from "../types";

export const useOrganizationStore = defineStore("iam-organization", () => {
  const organizations = ref<Organization[]>([]);
  const organizationTree = ref<Organization[]>([]);
  const currentOrganization = ref<Organization | null>(null);
  const organizationUsers = ref<OrganizationUser[]>([]);
  const loading = ref(false);

  const fetchOrganizations = async (params?: { keyword?: string; status?: string }) => {
    loading.value = true;
    try {
      const response = await getOrganizations(params);
      organizations.value = response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取组织列表失败"));
      console.error("fetchOrganizations error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchOrganizationTree = async () => {
    loading.value = true;
    try {
      const response = await getOrganizationTree();
      organizationTree.value = response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取组织树失败"));
      console.error("fetchOrganizationTree error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchOrganization = async (id: string) => {
    loading.value = true;
    try {
      const response = await getOrganization(id);
      currentOrganization.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取组织详情失败"));
      console.error("fetchOrganization error:", error);
    } finally {
      loading.value = false;
    }
  };

  const addOrganization = async (data: OrganizationCreate) => {
    loading.value = true;
    try {
      const response = await createOrganization(data);
      await fetchOrganizationTree(); // 刷新树
      notifySuccess("创建组织成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "创建组织失败"));
      console.error("addOrganization error:", error);
    } finally {
      loading.value = false;
    }
  };

  const editOrganization = async (id: string, data: OrganizationUpdate) => {
    loading.value = true;
    try {
      const response = await updateOrganization(id, data);
      await fetchOrganizationTree(); // 刷新树
      notifySuccess("更新组织成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "更新组织失败"));
      console.error("editOrganization error:", error);
    } finally {
      loading.value = false;
    }
  };

  const removeOrganization = async (id: string) => {
    loading.value = true;
    try {
      await deleteOrganization(id);
      await fetchOrganizationTree(); // 刷新树
      notifySuccess("删除组织成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "删除组织失败"));
      console.error("removeOrganization error:", error);
    } finally {
      loading.value = false;
    }
  };

  const updateLeader = async (id: string, leader_id: string) => {
    loading.value = true;
    try {
      await setOrganizationLeader(id, leader_id);
      await fetchOrganizationTree(); // 刷新树
      notifySuccess("设置组织负责人成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "设置组织负责人失败"));
      console.error("updateLeader error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchUsers = async (id: string) => {
    loading.value = true;
    try {
      const response = await getOrganizationUsers(id);
      organizationUsers.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取组织用户失败"));
      console.error("fetchUsers error:", error);
    } finally {
      loading.value = false;
    }
  };

  return {
    organizations,
    organizationTree,
    currentOrganization,
    organizationUsers,
    loading,
    fetchOrganizations,
    fetchOrganizationTree,
    fetchOrganization,
    addOrganization,
    editOrganization,
    removeOrganization,
    updateLeader,
    fetchUsers,
  };
});
