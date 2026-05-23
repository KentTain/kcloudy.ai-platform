<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { changePassword, getLoginHistory, updateCurrentUser } from "@/iam/api/auth";
import { useTenantStore } from "@/iam/stores/tenant";
import { getErrorMessage, notifyError, notifySuccess } from "@/iam/utils/feedback";
import { useUserStore } from "@/framework/stores";
import type { LoginHistory } from "@/iam/types";

const frameworkUserStore = useUserStore();
const tenantStore = useTenantStore();

const activeTab = ref("profile");

const profileForm = ref({
  nickname: frameworkUserStore.userInfo?.nickname || "",
  email: frameworkUserStore.userInfo?.email || "",
  phone: "",
});

const passwordForm = ref({
  old_password: "",
  new_password: "",
  confirm_password: "",
});

const loading = ref(false);
const profileLoading = ref(false);

// 登录历史状态
const loginHistory = ref<LoginHistory[]>([]);
const loginHistoryLoading = ref(false);
const loginHistoryTotal = ref(0);
const loginHistoryPage = ref(1);
const loginHistoryPageSize = ref(20);
const dateRange = ref<[string, string] | null>(null);

const handleProfileSubmit = async () => {
  profileLoading.value = true;
  try {
    const response = await updateCurrentUser(profileForm.value);
    const currentUserInfo = frameworkUserStore.userInfo;

    if (currentUserInfo) {
      frameworkUserStore.setUserInfo({
        ...currentUserInfo,
        username: response.data.username,
        nickname: response.data.nickname || currentUserInfo.nickname,
        avatar: response.data.avatar,
        email: response.data.email,
        roles: currentUserInfo.roles,
        permissions: currentUserInfo.permissions,
      });
    }

    notifySuccess("资料更新成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "资料更新失败"));
  } finally {
    profileLoading.value = false;
  }
};

const handlePasswordSubmit = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    notifyError("两次输入的密码不一致");
    return;
  }

  loading.value = true;
  try {
    await changePassword(
      passwordForm.value.old_password,
      passwordForm.value.new_password
    );
    notifySuccess("密码修改成功");
    passwordForm.value = {
      old_password: "",
      new_password: "",
      confirm_password: "",
    };
  } catch (error) {
    notifyError(getErrorMessage(error, "密码修改失败"));
  } finally {
    loading.value = false;
  }
};

const handleSwitchTenant = async (tenantId: string) => {
  try {
    await tenantStore.switchTenant(tenantId);
    notifySuccess("租户切换成功");
    // 刷新页面或重新加载数据
    window.location.reload();
  } catch (error) {
    notifyError(getErrorMessage(error, "租户切换失败"));
  }
};

// 加载登录历史
const loadLoginHistory = async () => {
  loginHistoryLoading.value = true;
  try {
    const params: Record<string, unknown> = {
      page: loginHistoryPage.value,
      page_size: loginHistoryPageSize.value,
    };

    if (dateRange.value && dateRange.value[0] && dateRange.value[1]) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }

    const response = await getLoginHistory(params);
    loginHistory.value = response.data.items;
    loginHistoryTotal.value = response.data.total;
  } catch (error) {
    notifyError(getErrorMessage(error, "获取登录历史失败"));
  } finally {
    loginHistoryLoading.value = false;
  }
};

// 监听页码变化
watch(loginHistoryPage, () => {
  loadLoginHistory();
});

// 监听日期范围变化
watch(dateRange, () => {
  loginHistoryPage.value = 1;
  loadLoginHistory();
});

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("zh-CN");
};

// 格式化设备类型
const formatDeviceType = (type?: string) => {
  const typeMap: Record<string, string> = {
    desktop: "桌面端",
    mobile: "移动端",
    tablet: "平板",
  };
  return type ? typeMap[type] || type : "-";
};

// 格式化登录状态
const formatLoginStatus = (status: string) => {
  return status === "success" ? "成功" : "失败";
};

// 监听 Tab 切换，加载登录历史
watch(activeTab, (newTab) => {
  if (newTab === "login-history") {
    loadLoginHistory();
  }
});

onMounted(async () => {
  await tenantStore.fetchMyTenants();
});
</script>

<template>
  <div class="profile-page">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="user-avatar">
            <el-avatar :size="80" :src="frameworkUserStore.userInfo?.avatar">
              {{ frameworkUserStore.userInfo?.username?.[0]?.toUpperCase() }}
            </el-avatar>
            <div class="username">
              {{ frameworkUserStore.userInfo?.username }}
            </div>
            <div class="roles">
              <el-tag
                v-for="role in frameworkUserStore.userInfo?.roles"
                :key="role"
                size="small"
              >
                {{ role }}
              </el-tag>
            </div>
          </div>

          <el-divider />

          <div class="tenant-info">
            <div class="label">当前租户</div>
            <div class="value">
              {{ tenantStore.currentTenant?.name || "默认租户" }}
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card shadow="never">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="个人资料" name="profile">
              <el-form
                :model="profileForm"
                label-width="100px"
                class="profile-form"
              >
                <el-form-item label="昵称">
                  <el-input v-model="profileForm.nickname" />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="profileForm.phone" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="profileLoading" @click="handleProfileSubmit">
                    保存
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="修改密码" name="password">
              <el-form
                :model="passwordForm"
                label-width="100px"
                class="password-form"
              >
                <el-form-item label="原密码">
                  <el-input
                    v-model="passwordForm.old_password"
                    type="password"
                    show-password
                  />
                </el-form-item>
                <el-form-item label="新密码">
                  <el-input
                    v-model="passwordForm.new_password"
                    type="password"
                    show-password
                  />
                </el-form-item>
                <el-form-item label="确认密码">
                  <el-input
                    v-model="passwordForm.confirm_password"
                    type="password"
                    show-password
                  />
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="loading"
                    @click="handlePasswordSubmit"
                  >
                    修改密码
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="切换租户" name="tenant">
              <el-table
                :data="tenantStore.myTenants"
                stripe
                v-loading="tenantStore.loading"
              >
                <el-table-column prop="tenant_name" label="租户名称" />
                <el-table-column prop="tenant_code" label="租户编码" />
                <el-table-column label="我的角色">
                  <template #default="{ row }">
                    {{ row.role_names?.join(", ") || "成员" }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button
                      type="primary"
                      size="small"
                      :disabled="row.is_current"
                      @click="handleSwitchTenant(row.tenant_id)"
                    >
                      切换
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="登录历史" name="login-history">
              <div class="login-history">
                <div class="login-history__filter">
                  <el-date-picker
                    v-model="dateRange"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    value-format="YYYY-MM-DD"
                    clearable
                  />
                </div>

                <el-table
                  :data="loginHistory"
                  stripe
                  v-loading="loginHistoryLoading"
                >
                  <el-table-column label="登录时间" min-width="180">
                    <template #default="{ row }">
                      {{ formatDateTime(row.login_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="ip_address" label="IP 地址" width="140" />
                  <el-table-column label="设备类型" width="100">
                    <template #default="{ row }">
                      {{ formatDeviceType(row.device_type) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="browser" label="浏览器" width="120">
                    <template #default="{ row }">
                      {{ row.browser || "-" }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="os" label="操作系统" width="120">
                    <template #default="{ row }">
                      {{ row.os || "-" }}
                    </template>
                  </el-table-column>
                  <el-table-column label="状态" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                        {{ formatLoginStatus(row.status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="location" label="位置" min-width="120">
                    <template #default="{ row }">
                      {{ row.location || "-" }}
                    </template>
                  </el-table-column>
                </el-table>

                <div class="login-history__pagination">
                  <el-pagination
                    v-model:current-page="loginHistoryPage"
                    v-model:page-size="loginHistoryPageSize"
                    :page-sizes="[10, 20, 50, 100]"
                    :total="loginHistoryTotal"
                    layout="total, sizes, prev, pager, next, jumper"
                  />
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.profile-page {
  padding: 16px;
}

.user-avatar {
  text-align: center;
  padding: 16px 0;
}

.username {
  margin-top: 12px;
  font-size: 18px;
  font-weight: 500;
}

.roles {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  gap: 8px;
}

.tenant-info {
  padding: 8px 0;
}

.tenant-info .label {
  font-size: 12px;
  color: #909399;
}

.tenant-info .value {
  font-size: 14px;
  margin-top: 4px;
}

.profile-form,
.password-form {
  max-width: 500px;
  margin-top: 16px;
}

.login-history {
  margin-top: 16px;
}

.login-history__filter {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.login-history__pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
