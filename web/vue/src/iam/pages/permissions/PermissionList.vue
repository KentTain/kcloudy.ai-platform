<script setup lang="ts">
import { ref, onMounted } from "vue";
import { usePermissionStore } from "@/iam/stores/permission";

const permissionStore = usePermissionStore();

const activeResource = ref("");

const loadPermissions = async () => {
  await permissionStore.fetchPermissionGroups();
};

const handleResourceChange = (resource: string) => {
  activeResource.value = resource;
};

onMounted(() => {
  loadPermissions();
});
</script>

<template>
  <div class="permission-list-page">
    <el-card shadow="never">
      <template #header>
        <span>权限管理</span>
      </template>

      <el-tabs v-model="activeResource" @tab-change="handleResourceChange">
        <el-tab-pane
          v-for="group in permissionStore.permissionGroups"
          :key="group.resource"
          :label="group.resource"
          :name="group.resource"
        >
          <el-table :data="group.permissions" stripe>
            <el-table-column prop="code" label="权限编码" min-width="150" />
            <el-table-column prop="name" label="权限名称" min-width="120" />
            <el-table-column prop="resource" label="资源" min-width="100" />
            <el-table-column prop="action" label="操作" min-width="80" />
            <el-table-column prop="description" label="描述" min-width="200" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.permission-list-page {
  padding: 16px;
}
</style>
