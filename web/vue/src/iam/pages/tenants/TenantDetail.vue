<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTenantStore } from "@/iam/stores/tenant";

const route = useRoute();
const router = useRouter();
const tenantStore = useTenantStore();

const tenantId = computed(() => route.params.id as string);

const loading = ref(false);

const loadTenantDetail = async () => {
  loading.value = true;
  try {
    await tenantStore.fetchTenant(tenantId.value);
  } finally {
    loading.value = false;
  }
};

const handleEdit = () => {
  router.push(`/tenants/${tenantId.value}/edit`);
};

const handleBack = () => {
  router.back();
};

const handleActivate = async () => {
  await tenantStore.activate(tenantId.value);
  await loadTenantDetail();
  alert("激活成功");
};

const handleDeactivate = async () => {
  await tenantStore.deactivate(tenantId.value);
  await loadTenantDetail();
  alert("停用成功");
};

onMounted(() => {
  loadTenantDetail();
});
</script>

<template>
  <div class="tenant-detail-page" v-loading="loading">
    <el-page-header @back="handleBack" content="租户详情">
      <template #extra>
        <el-button type="primary" @click="handleEdit">编辑</el-button>
        <el-button
          v-if="tenantStore.currentTenant?.status === 'inactive'"
          type="success"
          @click="handleActivate"
        >
          激活
        </el-button>
        <el-button
          v-if="tenantStore.currentTenant?.status === 'active'"
          @click="handleDeactivate"
        >
          停用
        </el-button>
      </template>
    </el-page-header>

    <el-card shadow="never" class="detail-card">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="租户名称">
          {{ tenantStore.currentTenant?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="租户编码">
          {{ tenantStore.currentTenant?.code }}
        </el-descriptions-item>
        <el-descriptions-item label="联系人">
          {{ tenantStore.currentTenant?.contact_name || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="联系人邮箱">
          {{ tenantStore.currentTenant?.contact_email || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="联系人电话">
          {{ tenantStore.currentTenant?.contact_phone || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="tenantStore.currentTenant?.status === 'active' ? 'success' : 'info'">
            {{ tenantStore.currentTenant?.status === 'active' ? '激活' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="过期时间">
          {{ tenantStore.currentTenant?.expired_at ? new Date(tenantStore.currentTenant.expired_at).toLocaleString() : '永久' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ tenantStore.currentTenant?.created_at ? new Date(tenantStore.currentTenant.created_at).toLocaleString() : '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.tenant-detail-page {
  padding: 16px;
}

.detail-card {
  margin-top: 16px;
}
</style>
