import { defineStore } from "pinia";
import { ref } from "vue";
import {
  createDepartment,
  deleteDepartment,
  getDepartment,
  getDepartmentTree,
  getDepartmentUsers,
  getDepartments,
  setDepartmentLeader,
  updateDepartment,
} from "../api/department";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { DepartmentCreate, Department, DepartmentUser, DepartmentUpdate } from "../types";

export const useDepartmentStore = defineStore("iam-department", () => {
  const departments = ref<Department[]>([]);
  const departmentTree = ref<Department[]>([]);
  const currentDepartment = ref<Department | null>(null);
  const departmentUsers = ref<DepartmentUser[]>([]);
  const loading = ref(false);

  const fetchDepartments = async (params?: { keyword?: string; status?: string }) => {
    loading.value = true;
    try {
      const response = await getDepartments(params);
      departments.value = response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取部门列表失败"));
      console.error("fetchDepartments error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchDepartmentTree = async () => {
    loading.value = true;
    try {
      const response = await getDepartmentTree();
      departmentTree.value = response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取部门树失败"));
      console.error("fetchDepartmentTree error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchDepartment = async (id: string) => {
    loading.value = true;
    try {
      const response = await getDepartment(id);
      currentDepartment.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取部门详情失败"));
      console.error("fetchDepartment error:", error);
    } finally {
      loading.value = false;
    }
  };

  const addDepartment = async (data: DepartmentCreate) => {
    loading.value = true;
    try {
      const response = await createDepartment(data);
      await fetchDepartmentTree(); // 刷新树
      notifySuccess("创建部门成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "创建部门失败"));
      console.error("addDepartment error:", error);
    } finally {
      loading.value = false;
    }
  };

  const editDepartment = async (id: string, data: DepartmentUpdate) => {
    loading.value = true;
    try {
      const response = await updateDepartment(id, data);
      await fetchDepartmentTree(); // 刷新树
      notifySuccess("更新部门成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "更新部门失败"));
      console.error("editDepartment error:", error);
    } finally {
      loading.value = false;
    }
  };

  const removeDepartment = async (id: string) => {
    loading.value = true;
    try {
      await deleteDepartment(id);
      await fetchDepartmentTree(); // 刷新树
      notifySuccess("删除部门成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "删除部门失败"));
      console.error("removeDepartment error:", error);
    } finally {
      loading.value = false;
    }
  };

  const updateLeader = async (id: string, leader_id: string) => {
    loading.value = true;
    try {
      await setDepartmentLeader(id, leader_id);
      await fetchDepartmentTree(); // 刷新树
      notifySuccess("设置部门负责人成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "设置部门负责人失败"));
      console.error("updateLeader error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchUsers = async (id: string) => {
    loading.value = true;
    try {
      const response = await getDepartmentUsers(id);
      departmentUsers.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取部门用户失败"));
      console.error("fetchUsers error:", error);
    } finally {
      loading.value = false;
    }
  };

  return {
    departments,
    departmentTree,
    currentDepartment,
    departmentUsers,
    loading,
    fetchDepartments,
    fetchDepartmentTree,
    fetchDepartment,
    addDepartment,
    editDepartment,
    removeDepartment,
    updateLeader,
    fetchUsers,
  };
});
