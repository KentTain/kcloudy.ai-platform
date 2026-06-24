<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";
import { toTypedSchema } from "@vee-validate/zod";
import { useForm } from "vee-validate";
import { z } from "zod";
import { Button, Input } from "@/components";
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components";
import { Loader2, Shield } from "@lucide/vue";

const router = useRouter();
const adminAuthStore = useAdminAuthStore();

const loginSchema = toTypedSchema(
  z.object({
    username: z.string().min(1, "请输入用户名"),
    password: z.string().min(1, "请输入密码"),
  }),
);

const { handleSubmit } = useForm({
  validationSchema: loginSchema,
  initialValues: {
    username: localStorage.getItem("last_admin_account") || "",
    password: "",
  },
});

const loading = ref(false);
const error = ref("");

const onSubmit = handleSubmit(async (values) => {
  loading.value = true;
  error.value = "";

  try {
    const success = await adminAuthStore.login({
      username: values.username,
      password: values.password,
    });

    if (success) {
      localStorage.setItem("last_admin_account", values.username);
      router.push("/admin/tenants");
    } else {
      error.value = "用户名或密码错误";
    }
  } catch (err: any) {
    error.value = err?.response?.data?.msg || err?.message || "登录失败，请重试";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="admin-login-page">
    <div class="admin-login-page__bg">
      <div class="admin-login-page__bg-gradient"></div>
    </div>

    <div class="admin-login-page__content">
      <div class="admin-login-page__card">
        <div class="admin-login-page__card-header">
          <div class="admin-login-page__logo">
            <Shield class="admin-login-page__logo-icon" />
            <span class="admin-login-page__logo-text">管理后台</span>
          </div>
          <h2 class="admin-login-page__card-title">管理员登录</h2>
          <p class="admin-login-page__card-desc">请使用管理员账号登录</p>
        </div>

        <form class="admin-login-page__form" @submit="onSubmit">
          <div v-if="error" class="admin-login-page__error">{{ error }}</div>

          <FormField v-slot="{ componentField }" name="username">
            <FormItem class="admin-login-page__field">
              <FormLabel>用户名</FormLabel>
              <FormControl>
                <Input v-bind="componentField" placeholder="请输入管理员用户名" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField v-slot="{ componentField }" name="password">
            <FormItem class="admin-login-page__field">
              <FormLabel>密码</FormLabel>
              <FormControl>
                <Input v-bind="componentField" type="password" placeholder="请输入密码" />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>

          <Button type="submit" class="admin-login-page__submit" :disabled="loading">
            <Loader2 v-if="loading" class="admin-login-page__loading-icon" />
            <span v-else>登录</span>
          </Button>
        </form>

        <div class="admin-login-page__footer">
          <p>默认管理员: tenant_admin / admin123</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  overflow: hidden;
}

.admin-login-page__bg {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 0;
}

.admin-login-page__bg-gradient {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.admin-login-page__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 2rem;
}

.admin-login-page__card {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.admin-login-page__card-header {
  text-align: center;
  margin-bottom: 2rem;
}

.admin-login-page__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.admin-login-page__logo-icon {
  width: 2rem;
  height: 2rem;
  color: #dc2626;
}

.admin-login-page__logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
}

.admin-login-page__card-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.5rem;
}

.admin-login-page__card-desc {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.admin-login-page__form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.admin-login-page__field {
  margin-bottom: 0;
}

.admin-login-page__error {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  color: #dc2626;
  font-size: 0.875rem;
  text-align: center;
}

.admin-login-page__submit {
  width: 100%;
  height: 2.75rem;
  font-size: 1rem;
  font-weight: 600;
}

.admin-login-page__loading-icon {
  width: 1.25rem;
  height: 1.25rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-login-page__footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  text-align: center;
}

.admin-login-page__footer p {
  margin: 0;
  font-size: 0.75rem;
  color: #9ca3af;
}
</style>
