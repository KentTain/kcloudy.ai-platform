import { defineStore } from "pinia";
import { ref } from "vue";
import {
  createUser,
  deleteUser,
  disableUser,
  enableUser,
  getUser,
  getUsers,
  lockUser,
  updateUser,
} from "../api/user";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { CreateUserParams, UpdateUserParams, User, UserQueryParams } from "../types";

export const useUserStore = defineStore("iam-user", () => {
  const users = ref<User[]>([]);
  const currentUser = ref<User | null>(null);
  const loading = ref(false);
  const total = ref(0);

  const fetchUsers = async (params?: UserQueryParams) => {
    loading.value = true;
    try {
      const response = await getUsers(params);
      users.value = response.data.items ?? [];
      total.value = response.data.total ?? 0;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取用户列表失败"));
      console.error("fetchUsers error:", error);
    } finally {
      loading.value = false;
    }
  };

  const fetchUser = async (id: string) => {
    loading.value = true;
    try {
      const response = await getUser(id);
      currentUser.value = response.data;
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取用户详情失败"));
      console.error("fetchUser error:", error);
    } finally {
      loading.value = false;
    }
  };

  const addUser = async (data: CreateUserParams) => {
    loading.value = true;
    try {
      const response = await createUser(data);
      users.value.unshift(response.data);
      total.value++;
      notifySuccess("创建用户成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "创建用户失败"));
      console.error("addUser error:", error);
    } finally {
      loading.value = false;
    }
  };

  const editUser = async (id: string, data: UpdateUserParams) => {
    loading.value = true;
    try {
      const response = await updateUser(id, data);
      const index = users.value.findIndex((u) => u.id === id);
      if (index !== -1) {
        users.value[index] = response.data;
      }
      notifySuccess("更新用户成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "更新用户失败"));
      console.error("editUser error:", error);
    } finally {
      loading.value = false;
    }
  };

  const removeUser = async (id: string) => {
    loading.value = true;
    try {
      await deleteUser(id);
      users.value = users.value.filter((u) => u.id !== id);
      total.value--;
      notifySuccess("删除用户成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "删除用户失败"));
      console.error("removeUser error:", error);
    } finally {
      loading.value = false;
    }
  };

  const changeUserStatus = async (id: string, status: "enable" | "disable" | "lock") => {
    loading.value = true;
    try {
      if (status === "enable") {
        await enableUser(id);
      } else if (status === "disable") {
        await disableUser(id);
      } else {
        await lockUser(id);
      }

      const user = users.value.find((u) => u.id === id);
      if (user) {
        user.status = status === "enable" ? "active" : status === "disable" ? "inactive" : "locked";
      }
      notifySuccess("更新用户状态成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "更新用户状态失败"));
      console.error("changeUserStatus error:", error);
    } finally {
      loading.value = false;
    }
  };

  return {
    users,
    currentUser,
    loading,
    total,
    fetchUsers,
    fetchUser,
    addUser,
    editUser,
    removeUser,
    changeUserStatus,
  };
});
