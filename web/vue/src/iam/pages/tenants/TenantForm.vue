<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTenantStore } from "@/iam/stores/tenant";
import type { CreateTenantParams, UpdateTenantParams } from "@/iam/types";

const route = useRoute();
const router = useRouter();
const tenantStore = useTenantStore();

const isEdit = computed(() => !!route.params.id);
const tenantId = computed(() => route.params.id as string);

const form = ref<CreateTenantParams & UpdateTenantParams>({
  name: "",
  code: "",
  contact_name: "",
  contact_email: "",
  contact_phone: "",
  expired_at: undefined,
});

const formRules = {
  name: [{ required: true, message: "请输入租户名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入租户编码", trigger: "blur" }],
};

const loading = ref(false);
const formRef = ref();

const handleSubmit = async () => {
  const valid = await formRef.value?.validate();
  if (!valid) return;

  loading.value = true;
  try {
    if (isEdit.value) {
      await tenantStore.editTenant(tenantId.value, form.value);
    } else {
      await tenantStore.addTenant(form.value);
    }
    alert(isEdit.value ? "保存成功" : "创建成功");
    router.back();
  } catch (error: any) {
    alert(error?.response?.data?.detail || "操作失败");
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  router.back();
};

onMounted(async () => {
  if (isEdit.value) {
    await tenantStore.fetchTenant(tenantId.value);
    const tenant = tenantStore.currentTenant;
    if (tenant) {
      form.value = {
        name: tenant.name,
        code: tenant.code,
        contact_name: tenant.contact_name || "",
        contact_email: tenant.contact_email || "",
        contact_phone: tenant.contact_phone || "",
        expired_at: tenant.expired_at,
      };
    }
  }
});
</script>

<template>
  <div class="tenant-form-page">
    <el-card shadow="never">
      <template #header>
        <span>{{ isEdit ? "编辑租户" : "创建租户" }}</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
        class="tenant-form"
      >
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="form.name" :disabled="isEdit" />
        </el-form-item>

        <el-form-item label="租户编码" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" />
        </el-form-item>

        <el-form-item label="联系人" prop="contact_name">
          <el-input v-model="form.contact_name" />
        </el-form-item>

        <el-form-item label="联系人邮箱" prop="contact_email">
          <el-input v-model="form.contact_email" />
        </el-form-item>

        <el-form-item label="联系人电话" prop="contact_phone">
          <el-input v-model="form.contact_phone" />
        </el-form-item>

        <el-form-item label="过期时间" prop="expired_at">
          <el-date-picker
            v-model="form.expired_at"
            type="datetime"
            placeholder="选择日期时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
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
.tenant-form-page {
  padding: 16px;
}

.tenant-form {
  max-width: 600px;
}
</style>
