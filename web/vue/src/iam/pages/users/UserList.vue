<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/iam/stores/user";
import { useUserStore as useFrameworkUserStore } from "@/framework/stores";
import type { User } from "@/iam/types";
import { confirmAction } from "@/iam/utils/feedback";

const router = useRouter();
const userStore = useUserStore();
const frameworkUserStore = useFrameworkUserStore();

const searchForm = ref({
  keyword: "",
  status: "",
});

const pagination = ref({
  page: 1,
  page_size: 20,
});

const handleSearch = () => {
  pagination.value.page = 1;
  loadUsers();
};

const loadUsers = async () => {
  await userStore.fetchUsers({
    page: pagination.value.page,
    page_size: pagination.value.page_size,
    keyword: searchForm.value.keyword || undefined,
    status: searchForm.value.status || undefined,
  });
};

const handlePageChange = (page: number) => {
  pagination.value.page = page;
  loadUsers();
};

const handleSizeChange = (size: number) => {
  pagination.value.page_size = size;
  pagination.value.page = 1;
  loadUsers();
};

const handleCreate = () => {
  router.push("/users/create");
};

const handleEdit = (row: User) => {
  router.push(`/users/${row.id}/edit`);
};

const handleDelete = async (row: User) => {
  if (!confirmAction(`确定要删除用户 "${row.username}" 吗？`)) return;

  await userStore.removeUser(row.id);
};

const handleStatusChange = async (row: User, status: "enable" | "disable" | "lock") => {
  await userStore.changeUserStatus(row.id, status);
};

// 检查权限
const canCreate = computed(() => frameworkUserStore.hasPermission("user:add"));
const canEdit = computed(() => frameworkUserStore.hasPermission("user:edit"));
const canDelete = computed(() => frameworkUserStore.hasPermission("user:delete"));

onMounted(() => {
  loadUsers();
});
</script>

<template>
  <div class="user-list-page">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键字">
          <el-input
            v-model="searchForm.keyword"
            placeholder="用户名/邮箱/手机号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="激活" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="锁定" value="locked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="searchForm = { keyword: '', status: '' }">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <span>用户列表</span>
          <el-button v-if="canCreate" type="primary" @click="handleCreate">
            新建用户
          </el-button>
        </div>
      </template>

      <!-- 表格 -->
      <el-table :data="userStore.users" v-loading="userStore.loading" stripe>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="100" />
        <el-table-column prop="email" label="邮箱" min-width="150" />
        <el-table-column prop="phone" label="手机号" min-width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : row.status === 'locked' ? 'danger' : 'info'">
              {{ row.status === 'active' ? '激活' : row.status === 'locked' ? '锁定' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEdit" link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="canEdit && row.status === 'active'" link @click="handleStatusChange(row, 'disable')">
              停用
            </el-button>
            <el-button v-if="canEdit && row.status === 'inactive'" link type="success" @click="handleStatusChange(row, 'enable')">
              激活
            </el-button>
            <el-button v-if="canEdit && row.status !== 'locked'" link type="danger" @click="handleStatusChange(row, 'lock')">
              锁定
            </el-button>
            <el-button v-if="canDelete" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="userStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.user-list-page {
  padding: 16px;
}

.search-card {
  margin-bottom: 16px;
}

.table-card :deep(.table-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
