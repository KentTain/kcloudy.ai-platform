<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useTenantStore } from "@/iam/stores/tenant";
import { useUserStore } from "@/framework/stores";
import type { Tenant } from "@/iam/types";
import { confirmAction, notifySuccess } from "@/iam/utils/feedback";

const router = useRouter();
const tenantStore = useTenantStore();
const frameworkUserStore = useUserStore();

const searchForm = ref({
  keyword: "",
  status: "",
});

const pagination = ref({
  page: 1,
  page_size: 20,
});

const loadTenants = async () => {
  await tenantStore.fetchTenants({
    page: pagination.value.page,
    page_size: pagination.value.page_size,
    keyword: searchForm.value.keyword || undefined,
    status: searchForm.value.status || undefined,
  });
};

const handleSearch = () => {
  pagination.value.page = 1;
  loadTenants();
};

const handleCreate = () => {
  router.push("/tenants/create");
};

const handleEdit = (row: Tenant) => {
  router.push(`/tenants/${row.id}/edit`);
};

const handleDelete = async (row: Tenant) => {
  if (!confirmAction(`确定要删除租户 "${row.name}" 吗？`)) return;

  await tenantStore.removeTenant(row.id);
  notifySuccess("删除成功");
};

const handleActivate = async (row: Tenant) => {
  await tenantStore.activate(row.id);
  notifySuccess("激活成功");
};

const handleDeactivate = async (row: Tenant) => {
  await tenantStore.deactivate(row.id);
  notifySuccess("停用成功");
};

const canCreate = computed(() => frameworkUserStore.hasRole("tenant_admin"));
const canEdit = computed(() => frameworkUserStore.hasRole("tenant_admin"));

onMounted(() => {
  loadTenants();
});
</script>

<template>
  <div class="tenant-list-page">
    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <span>租户管理</span>
          <el-button v-if="canCreate" type="primary" @click="handleCreate">
            新建租户
          </el-button>
        </div>
      </template>

      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="关键字">
          <el-input
            v-model="searchForm.keyword"
            placeholder="租户名称/编码"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="激活" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="tenantStore.tenants"
        v-loading="tenantStore.loading"
        stripe
      >
        <el-table-column prop="name" label="租户名称" min-width="120" />
        <el-table-column prop="code" label="租户编码" min-width="120" />
        <el-table-column prop="contact_name" label="联系人" min-width="100" />
        <el-table-column
          prop="contact_email"
          label="联系人邮箱"
          min-width="150"
        />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === "active" ? "激活" : "停用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="expired_at" label="过期时间" width="180">
          <template #default="{ row }">
            {{
              row.expired_at
                ? new Date(row.expired_at).toLocaleDateString()
                : "永久"
            }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="canEdit"
              link
              type="primary"
              @click="handleEdit(row)"
              >编辑</el-button
            >
            <el-button
              v-if="canEdit && row.status === 'inactive'"
              link
              type="success"
              @click="handleActivate(row)"
            >
              激活
            </el-button>
            <el-button
              v-if="canEdit && row.status === 'active'"
              link
              @click="handleDeactivate(row)"
            >
              停用
            </el-button>
            <el-button
              v-if="canEdit"
              link
              type="danger"
              @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="tenantStore.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadTenants"
          @size-change="loadTenants"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.tenant-list-page {
  padding: 16px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 16px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
