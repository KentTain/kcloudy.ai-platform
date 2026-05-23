<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useRoleStore } from "@/iam/stores/role";
import { useUserStore } from "@/framework/stores";
import type { Role } from "@/iam/types";
import { confirmAction, notifyError } from "@/iam/utils/feedback";

const router = useRouter();
const roleStore = useRoleStore();
const frameworkUserStore = useUserStore();

const pagination = ref({
  page: 1,
  page_size: 20,
});

const loadRoles = async () => {
  await roleStore.fetchRoles({
    page: pagination.value.page,
    page_size: pagination.value.page_size,
  });
};

const handleCreate = () => {
  router.push("/roles/create");
};

const handleEdit = (row: Role) => {
  router.push(`/roles/${row.id}`);
};

const handleDelete = async (row: Role) => {
  if (row.is_system) {
    notifyError("系统内置角色无法删除");
    return;
  }
  if (!confirmAction(`确定要删除角色 "${row.name}" 吗？`)) return;

  await roleStore.removeRole(row.id);
};

const canCreate = computed(() => frameworkUserStore.hasPermission("role:add"));
const canEdit = computed(() => frameworkUserStore.hasPermission("role:edit"));
const canDelete = computed(() => frameworkUserStore.hasPermission("role:delete"));

onMounted(() => {
  loadRoles();
});
</script>

<template>
  <div class="role-list-page">
    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <span>角色列表</span>
          <el-button v-if="canCreate" type="primary" @click="handleCreate">
            新建角色
          </el-button>
        </div>
      </template>

      <el-table :data="roleStore.roles" v-loading="roleStore.loading" stripe>
        <el-table-column prop="code" label="角色编码" min-width="120" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="is_system" label="系统角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_system ? 'warning' : 'info'">
              {{ row.is_system ? "是" : "否" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEdit" link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="canDelete && !row.is_system" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="roleStore.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadRoles"
          @size-change="loadRoles"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.role-list-page {
  padding: 16px;
}

.table-header {
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
