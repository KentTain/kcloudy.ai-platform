<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/iam/stores/auth";
import { toTypedSchema } from "@vee-validate/zod";
import { useForm } from "vee-validate";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Loader2 } from "@lucide/vue";

const router = useRouter();
const authStore = useAuthStore();

const loginSchema = toTypedSchema(
  z.object({
    username: z.string().min(1, "请输入用户名"),
    password: z.string().min(1, "请输入密码"),
  }),
);

const { handleSubmit } = useForm({
  validationSchema: loginSchema,
  initialValues: {
    username: localStorage.getItem("last_login_account") || "",
    password: "",
  },
});

const loading = ref(false);
const error = ref("");

const onSubmit = handleSubmit(async (values) => {
  loading.value = true;
  error.value = "";

  try {
    await authStore.login({
      account: values.username,
      password: values.password,
    });
    localStorage.setItem("last_login_account", values.username);
    router.push("/");
  } catch (err: any) {
    error.value = err?.response?.data?.msg || err?.message || "登录失败，请重试";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="login-page">
    <div class="login-page__grid">
      <!-- Brand section - hidden on small screens -->
      <div class="login-page__brand">
        <div class="login-page__brand-content">
          <h1 class="login-page__brand-title">AI 助手平台</h1>
          <p class="login-page__brand-desc">智能、高效、安全的企业级 AI 助手解决方案</p>
        </div>
      </div>

      <!-- Form section -->
      <div class="login-page__form-section">
        <Card>
          <CardHeader>
            <CardTitle>登录</CardTitle>
          </CardHeader>
          <CardContent>
            <form class="login-page__form" @submit="onSubmit">
              <div v-if="error" class="login-page__error">{{ error }}</div>

              <FormField v-slot="{ componentField }" name="username">
                <FormItem>
                  <FormLabel>用户名</FormLabel>
                  <FormControl>
                    <Input v-bind="componentField" placeholder="请输入用户名" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              </FormField>

              <FormField v-slot="{ componentField }" name="password">
                <FormItem>
                  <FormLabel>密码</FormLabel>
                  <FormControl>
                    <Input v-bind="componentField" type="password" placeholder="请输入密码" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              </FormField>

              <Button type="submit" class="w-full" :disabled="loading">
                <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
                登录
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--color-surface);
}

.login-page__grid {
  display: grid;
  grid-template-columns: 1fr;
  width: 100%;
  max-width: 1000px;
  gap: 0;
}

.login-page__brand {
  display: none;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary) 60%, #6366f1);
  color: #fff;
  padding: 3rem;
}

.login-page__brand-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  min-height: 100vh;
}

.login-page__brand-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
}

.login-page__brand-desc {
  font-size: 1rem;
  margin: 1rem 0 0;
  opacity: 0.9;
}

.login-page__form-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-page__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-page__error {
  color: var(--color-danger);
  font-size: 0.875rem;
  text-align: center;
  padding: 0.5rem;
  border-radius: 0.25rem;
  background-color: rgba(239, 68, 68, 0.1);
}

@media (min-width: 1024px) {
  .login-page__grid {
    grid-template-columns: 1fr 1fr;
  }

  .login-page__brand {
    display: flex;
  }
}
</style>