<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/iam/stores/user";
import type { CreateUserParams, UpdateUserParams } from "@/iam/types";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const isEdit = computed(() => !!route.params.id);
const userId = computed(() => route.params.id as string);

type UserFormModel = Omit<CreateUserParams, "password"> &
  Partial<Pick<CreateUserParams, "password">> &
  UpdateUserParams;

const form = ref<UserFormModel>({
  username: "",
  password: "",
  email: "",
  phone: "",
  nickname: "",
});

const formRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 50, message: "用户名长度为 3-50 个字符", trigger: "blur" },
  ],
  password: [
    { required: !isEdit.value, message: "请输入密码", trigger: "blur" },
    { min: 8, max: 32, message: "密码长度为 8-32 个字符", trigger: "blur" },
  ],
};

const loading = ref(false);
const formRef = ref();

const handleSubmit = async () => {
  const valid = await formRef.value?.validate();
  if (!valid) return;

  loading.value = true;
  try {
    if (isEdit.value) {
      const submitData: UpdateUserParams = {
        email: form.value.email,
        phone: form.value.phone,
        nickname: form.value.nickname,
      };
      await userStore.editUser(userId.value, submitData);
    } else {
      const submitData: CreateUserParams = {
        username: form.value.username,
        password: form.value.password || "",
        email: form.value.email,
        phone: form.value.phone,
        nickname: form.value.nickname,
        role_ids: form.value.role_ids,
        department_id: form.value.department_id,
      };
      await userStore.addUser(submitData);
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
  if (isEdit.value) {
    await userStore.fetchUser(userId.value);
    const user = userStore.currentUser;
    if (user) {
      form.value = {
        username: user.username,
        email: user.email || "",
        phone: user.phone || "",
        nickname: user.nickname || "",
      };
    }
  }
});
</script>

<template>
  <div class="user-form-page">
    <el-card shadow="never">
      <template #header>
        <span>{{ isEdit ? "编辑用户" : "创建用户" }}</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        class="user-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>

        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>

        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
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
.user-form-page {
  padding: 16px;
}

.user-form {
  max-width: 600px;
}
</style>
