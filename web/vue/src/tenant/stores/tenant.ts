import { defineStore } from "pinia";
import { computed, ref } from "vue";
import {
  activateTenant,
  createTenant,
  deactivateTenant,
  deleteTenant,
  getCurrentTenant,
  getMyTenants,
  getTenant,
  getTenants,
  switchTenant as switchTenantApi,
  updateTenant,
} from "../api/tenant";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { TenantCreate, Tenant, TenantListStats, TenantUpdate, UserTenantResponse } from "../types";

export const useTenantStore = defineStore("tenant", () => {
  const tenants = ref<Tenant[]>([]);
  const currentTenant = ref<Tenant | null>(null);
  const myTenants = ref<UserTenantResponse[]>([]);
  const loading = ref(false);
  const total = ref(0);
  const stats = ref<TenantListStats>({
    total_count: 0,
    inactive_count: 0,
    expired_count: 0,
  });

  // 管理员：获取租户列表
  const fetchTenants = async (params?: {
    page?: number;
    page_size?: number;
    keyword?: string;
    status?: string;
  }) => {
    loading.value = true;
    try {
      const response = await getTenants(params);
      tenants.value = response.data.items ?? [];
      total.value = response.data.total ?? 0;
      stats.value = response.data.stats ?? {
        total_count: 0,
        inactive_count: 0,
        expired_count: 0,
      };
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "获取租户列表失败"));
      console.error("fetchTenants error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 管理员：获取租户详情
  const fetchTenant = async (id: string) => {
    loading.value = true;
    try {
      const response = await getTenant(id);
      currentTenant.value = response.data;
      return response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "获取租户详情失败"));
      console.error("fetchTenant error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 管理员：创建租户
  const addTenant = async (data: TenantCreate) => {
    loading.value = true;
    try {
      const response = await createTenant(data);
      tenants.value.unshift(response.data);
      total.value++;
      notifySuccess("创建租户成功");
      return response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "创建租户失败"));
      console.error("addTenant error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 管理员：更新租户
  const editTenant = async (id: string, data: TenantUpdate) => {
    loading.value = true;
    try {
      const response = await updateTenant(id, data);
      const index = tenants.value.findIndex((t) => t.id === id);
      if (index !== -1) {
        tenants.value[index] = response.data;
      }
      notifySuccess("更新租户成功");
      return response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "更新租户失败"));
      console.error("editTenant error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 管理员：删除租户
  const removeTenant = async (id: string) => {
    loading.value = true;
    try {
      await deleteTenant(id);
      tenants.value = tenants.value.filter((t) => t.id !== id);
      total.value--;
      notifySuccess("删除租户成功");
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "删除租户失败"));
      console.error("removeTenant error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 激活租户
  const activate = async (id: string) => {
    loading.value = true;
    try {
      const response = await activateTenant(id);
      const index = tenants.value.findIndex((t) => t.id === id);
      if (index !== -1) {
        tenants.value[index] = response.data;
      }
      if (currentTenant.value?.id === id) {
        currentTenant.value = response.data;
      }
      notifySuccess("激活租户成功");
      return response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "激活租户失败"));
      console.error("activate error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 停用租户
  const deactivate = async (id: string) => {
    loading.value = true;
    try {
      const response = await deactivateTenant(id);
      const index = tenants.value.findIndex((t) => t.id === id);
      if (index !== -1) {
        tenants.value[index] = response.data;
      }
      if (currentTenant.value?.id === id) {
        currentTenant.value = response.data;
      }
      notifySuccess("停用租户成功");
      return response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "停用租户失败"));
      console.error("deactivate error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 控制台：获取当前租户
  const fetchCurrentTenant = async () => {
    loading.value = true;
    try {
      const response = await getCurrentTenant();
      currentTenant.value = response.data;
      return response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "获取当前租户失败"));
      console.error("fetchCurrentTenant error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 控制台：获取用户可切换的租户列表
  const fetchMyTenants = async () => {
    loading.value = true;
    try {
      const response = await getMyTenants();
      myTenants.value = response.data;
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "获取我的租户列表失败"));
      console.error("fetchMyTenants error:", error);
    } finally {
      loading.value = false;
    }
  };

  // 控制台：切换租户
  const switchTenant = async (tenant_id: string) => {
    loading.value = true;
    try {
      await switchTenantApi(tenant_id);
      await fetchCurrentTenant();
      notifySuccess("切换租户成功");
    } catch (error: unknown) {
      notifyError(getErrorMessage(error, "切换租户失败"));
      console.error("switchTenant error:", error);
    } finally {
      loading.value = false;
    }
  };

  const isCurrentTenantActive = computed(() => currentTenant.value?.status === "active");

  return {
    tenants,
    currentTenant,
    myTenants,
    loading,
    total,
    stats,
    fetchTenants,
    fetchTenant,
    addTenant,
    editTenant,
    removeTenant,
    activate,
    deactivate,
    fetchCurrentTenant,
    fetchMyTenants,
    switchTenant,
    isCurrentTenantActive,
  };
});
