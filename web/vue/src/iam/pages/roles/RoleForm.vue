<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useRoleStore } from "@/iam/stores/role";
import { usePermissionStore } from "@/iam/stores/permission";
import PermissionTree from "@/iam/components/PermissionTree.vue";
import type { CreateRoleParams, UpdateRoleParams } from "@/iam/types";

const route = useRoute();
const router = useRouter();
const roleStore = useRoleStore();
const permissionStore = usePermissionStore();

const isEdit = computed(() => !!route.params.id);
const roleId = computed(() => route.params.id as string);

const form = ref<CreateRoleParams & UpdateRoleParams>({
  code: "",
  name: "",
  description: "",
});

const formRules = {
  code: [{ required: true, message: "请输入角色编码", trigger: "blur" }],
  name: [{ required: true, message: "请输入角色名称", trigger: "blur" }],
};

const selectedPermissions = ref<string[]>([]);
const loading = ref(false);
const formRef = ref();

const handleSubmit = async () => {
  const valid = await formRef.value?.validate();
  if (!valid) return;

  loading.value = true;
  try {
    if (isEdit.value) {
      await roleStore.editRole(roleId.value, form.value);
      await roleStore.updateRolePermissions(roleId.value, selectedPermissions.value);
    } else {
      const newRole = await roleStore.addRole(form.value);
      if (newRole) {
        await roleStore.updateRolePermissions(newRole.id, selectedPermissions.value);
      }
    }
    router.back();
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  router.back();
};

onMounted(async () => {
  // 加载所有权限
  await permissionStore.fetchAllPermissions();

  if (isEdit.value) {
    await roleStore.fetchRole(roleId.value);
    await roleStore.fetchRolePermissions(roleId.value);

    const role = roleStore.currentRole;
    if (role) {
      form.value = {
        code: role.code,
        name: role.name,
        description: role.description || "",
      };
    }
    selectedPermissions.value = roleStore.currentRolePermissions.map(p => p.id);
  }
});
</script>

<template>
  <div class="role-form-page">
    <el-card shadow="never">
      <template #header>
        <span>{{ isEdit ? "编辑角色" : "创建角色" }}</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        class="role-form"
      >
        <el-form-item label="角色编码" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" />
        </el-form-item>

        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>

        <el-form-item label="权限分配">
          <div class="permission-tree-container">
            <PermissionTree
              v-model="selectedPermissions"
              :permissions="permissionStore.permissions"
            />
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            {{ isEdit ? "保存" : "创建" }}
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.role-form-page {
  padding: 16px;
}

.role-form {
  max-width: 800px;
}

.permission-tree-container {
  width: 100%;
  max-height: 400px;
  overflow: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
}
</style>
