<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getDepartments } from "@/iam/api/department";
import { getRoles } from "@/iam/api/role";
import {
  assignUserDepartments,
  assignUserRoles,
  getUserDepartments,
  getUserRoles,
  resetUserPassword,
} from "@/iam/api/user";
import { useUserStore } from "@/iam/stores/user";
import type { Department, Role } from "@/iam/types";
import { getErrorMessage, notifyError, notifySuccess } from "@/iam/utils/feedback";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const userId = computed(() => route.params.id as string);
const roles = ref<Role[]>([]);
const departments = ref<Department[]>([]);
const allRoles = ref<Role[]>([]);
const allDepartments = ref<Department[]>([]);
const selectedRoleIds = ref<string[]>([]);
const selectedDepartmentIds = ref<string[]>([]);
const loading = ref(false);
const savingRoles = ref(false);
const savingDepartments = ref(false);
const resettingPassword = ref(false);

const loadUserDetail = async () => {
  loading.value = true;
  try {
    await userStore.fetchUser(userId.value);
    const [rolesRes, deptsRes, allRolesRes, allDepartmentsRes] = await Promise.all([
      getUserRoles(userId.value),
      getUserDepartments(userId.value),
      getRoles({ page: 1, page_size: 100 }),
      getDepartments(),
    ]);
    roles.value = rolesRes.data;
    departments.value = deptsRes.data;
    selectedRoleIds.value = rolesRes.data.map((role) => role.id);
    selectedDepartmentIds.value = deptsRes.data.map((dept) => dept.id);
    allRoles.value = allRolesRes.data.items;
    allDepartments.value = allDepartmentsRes.data;
  } catch (error) {
    notifyError(getErrorMessage(error, "加载用户详情失败"));
  } finally {
    loading.value = false;
  }
};

const handleEdit = () => {
  router.push(`/users/${userId.value}/edit`);
};

const handleBack = () => {
  router.back();
};

const handleResetPassword = async () => {
  resettingPassword.value = true;
  try {
    const response = await resetUserPassword(userId.value);
    notifySuccess(`密码重置成功，新密码：${response.data.password}`);
  } catch (error) {
    notifyError(getErrorMessage(error, "重置密码失败"));
  } finally {
    resettingPassword.value = false;
  }
};

const handleSaveRoles = async () => {
  savingRoles.value = true;
  try {
    await assignUserRoles(userId.value, selectedRoleIds.value);
    const rolesRes = await getUserRoles(userId.value);
    roles.value = rolesRes.data;
    selectedRoleIds.value = rolesRes.data.map((role) => role.id);
    notifySuccess("角色分配保存成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "角色分配保存失败"));
  } finally {
    savingRoles.value = false;
  }
};

const handleSaveDepartments = async () => {
  savingDepartments.value = true;
  try {
    await assignUserDepartments(userId.value, selectedDepartmentIds.value);
    const deptsRes = await getUserDepartments(userId.value);
    departments.value = deptsRes.data;
    selectedDepartmentIds.value = deptsRes.data.map((dept) => dept.id);
    notifySuccess("部门分配保存成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "部门分配保存失败"));
  } finally {
    savingDepartments.value = false;
  }
};

onMounted(() => {
  loadUserDetail();
});
</script>

<template>
  <div class="user-detail-page" v-loading="loading">
    <el-page-header @back="handleBack" content="用户详情">
      <template #extra>
        <el-button :loading="resettingPassword" @click="handleResetPassword">重置密码</el-button>
        <el-button type="primary" @click="handleEdit">编辑</el-button>
      </template>
    </el-page-header>

    <el-card shadow="never" class="detail-card">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">
          {{ userStore.currentUser?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="昵称">
          {{ userStore.currentUser?.nickname || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ userStore.currentUser?.email || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="手机号">
          {{ userStore.currentUser?.phone || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="userStore.currentUser?.status === 'active' ? 'success' : 'info'">
            {{ userStore.currentUser?.status === 'active' ? '激活' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ userStore.currentUser?.created_at ? new Date(userStore.currentUser.created_at).toLocaleString() : "-" }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="detail-card">
      <template #header>
        <span>角色</span>
      </template>
      <el-space wrap>
        <el-tag v-for="role in roles" :key="role.id">{{ role.name }}</el-tag>
        <span v-if="roles.length === 0" class="empty-text">暂无</span>
      </el-space>
    </el-card>

    <el-card shadow="never" class="detail-card">
      <template #header>
        <div class="section-header">
          <span>角色分配</span>
          <el-button type="primary" :loading="savingRoles" @click="handleSaveRoles">保存角色</el-button>
        </div>
      </template>
      <el-select
        v-model="selectedRoleIds"
        multiple
        filterable
        collapse-tags
        collapse-tags-tooltip
        placeholder="请选择角色"
        class="full-width"
      >
        <el-option v-for="role in allRoles" :key="role.id" :label="role.name" :value="role.id" />
      </el-select>
    </el-card>

    <el-card shadow="never" class="detail-card">
      <template #header>
        <span>部门</span>
      </template>
      <el-space wrap>
        <el-tag v-for="dept in departments" :key="dept.id">{{ dept.name }}</el-tag>
        <span v-if="departments.length === 0" class="empty-text">暂无</span>
      </el-space>
    </el-card>

    <el-card shadow="never" class="detail-card">
      <template #header>
        <div class="section-header">
          <span>部门分配</span>
          <el-button type="primary" :loading="savingDepartments" @click="handleSaveDepartments">
            保存部门
          </el-button>
        </div>
      </template>
      <el-select
        v-model="selectedDepartmentIds"
        multiple
        filterable
        collapse-tags
        collapse-tags-tooltip
        placeholder="请选择部门"
        class="full-width"
      >
        <el-option v-for="dept in allDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
      </el-select>
    </el-card>
  </div>
</template>

<style scoped>
.user-detail-page {
  padding: 16px;
}

.detail-card {
  margin-top: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.full-width {
  width: 100%;
}

.empty-text {
  color: #909399;
  font-size: 14px;
}
</style>
