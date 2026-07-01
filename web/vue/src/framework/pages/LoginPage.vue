<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/iam/stores/auth";
import { toTypedSchema } from "@vee-validate/zod";
import { useForm } from "vee-validate";
import { z } from "zod";
import { Button, Input } from "@/components";
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components";
import { Loader2, Sparkles, Shield, Zap } from "@lucide/vue";

const router = useRouter();
const authStore = useAuthStore();

const loginSchema = toTypedSchema(
  z.object({
    username: z.string().min(1, "请输入用户名"),
    password: z.string().min(1, "请输入密码"),
  }),
);

const { handleSubmit, setFieldError } = useForm({
  validationSchema: loginSchema,
  initialValues: {
    username: localStorage.getItem("last_login_account") || "",
    password: "",
  },
});

const loading = ref(false);

const onSubmit = handleSubmit(async (values) => {
  loading.value = true;

  try {
    await authStore.login({
      account: values.username,
      password: values.password,
    });
    localStorage.setItem("last_login_account", values.username);
    router.push("/");
  } catch (err: any) {
    const message = err?.response?.data?.msg || err?.message || "登录失败，请重试";
    setFieldError("password", message);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="login-page">
    <div class="login-page__bg">
      <div class="login-page__bg-gradient"></div>
      <div class="login-page__bg-pattern"></div>
      <div class="login-page__bg-orb login-page__bg-orb--1"></div>
      <div class="login-page__bg-orb login-page__bg-orb--2"></div>
      <div class="login-page__bg-orb login-page__bg-orb--3"></div>
    </div>

    <div class="login-page__content">
      <div class="login-page__brand">
        <div class="login-page__brand-inner">
          <div class="login-page__logo">
            <Sparkles class="login-page__logo-icon" />
            <span class="login-page__logo-text">AI 助手平台</span>
          </div>
          <h1 class="login-page__title">智能办公新体验</h1>
          <p class="login-page__subtitle">安全、高效、智能的企业级 AI 助手解决方案</p>
          
          <div class="login-page__features">
            <div class="login-page__feature">
              <Shield class="login-page__feature-icon" />
              <span>企业级安全</span>
            </div>
            <div class="login-page__feature">
              <Zap class="login-page__feature-icon" />
              <span>极速响应</span>
            </div>
            <div class="login-page__feature">
              <Sparkles class="login-page__feature-icon" />
              <span>智能对话</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login-page__form-container">
        <div class="login-page__card">
          <div class="login-page__card-header">
            <h2 class="login-page__card-title">欢迎回来</h2>
            <p class="login-page__card-desc">请登录您的账号继续</p>
          </div>

          <form class="login-page__form" @submit="onSubmit">
            <FormField v-slot="{ componentField }" name="username">
              <FormItem class="login-page__field">
                <FormLabel>用户名</FormLabel>
                <FormControl>
                  <Input v-bind="componentField" placeholder="请输入用户名" />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField v-slot="{ componentField }" name="password">
              <FormItem class="login-page__field">
                <FormLabel>密码</FormLabel>
                <FormControl>
                  <Input v-bind="componentField" type="password" placeholder="请输入密码" />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <Button type="submit" class="login-page__submit" :disabled="loading">
              <Loader2 v-if="loading" class="login-page__loading-icon" />
              <span v-else>登录</span>
            </Button>
          </form>

          <div class="login-page__footer">
            <p>首次使用？请联系管理员开通账号</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  overflow: hidden;
}

.login-page__bg {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 0;
}

.login-page__bg-gradient {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: linear-gradient(135deg, #f0f5ff 0%, #e6edff 50%, #dde8ff 100%);
}

.login-page__bg-pattern {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-image: radial-gradient(circle at 1px 1px, rgba(100, 130, 180, 0.15) 1px, transparent 0);
  background-size: 40px 40px;
}

.login-page__bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s infinite ease-in-out;
}

.login-page__bg-orb--1 {
  top: -10%;
  left: -5%;
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #6b8cce 0%, #7c9fe0 100%);
}

.login-page__bg-orb--2 {
  top: 50%;
  right: -10%;
  width: 350px;
  height: 350px;
  background: linear-gradient(135deg, #5ba3d9 0%, #6bc4e8 100%);
  animation-delay: -7s;
}

.login-page__bg-orb--3 {
  bottom: -15%;
  left: 30%;
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #4ac2b8 0%, #5dd4c8 100%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

.login-page__content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  gap: 3rem;
}

@media (min-width: 1024px) {
  .login-page__content {
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    padding: 4rem;
  }
}

.login-page__brand {
  display: none;
  align-items: center;
}

@media (min-width: 1024px) {
  .login-page__brand {
    display: flex;
  }
}

.login-page__brand-inner {
  max-width: 480px;
}

.login-page__logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.login-page__logo-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: #1677ff;
}

.login-page__logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.login-page__title {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.2;
  margin: 0 0 1rem;
  background: linear-gradient(135deg, #1a365d 0%, #1677ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-page__subtitle {
  font-size: 1.125rem;
  color: #4b5563;
  margin: 0 0 3rem;
  line-height: 1.6;
}

.login-page__features {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.login-page__feature {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1rem;
  color: #374151;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 0.75rem;
  backdrop-filter: blur(10px);
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.login-page__feature:hover {
  transform: translateX(4px);
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.15);
}

.login-page__feature-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #1677ff;
}

.login-page__form-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-page__card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 1.5rem;
  backdrop-filter: blur(20px);
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

.login-page__card-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-page__card-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.5rem;
}

.login-page__card-desc {
  font-size: 0.9375rem;
  color: #6b7280;
  margin: 0;
}

.login-page__form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.login-page__field {
  margin-bottom: 0;
  max-height: 64px;
}

.login-page__submit {
  width: 100%;
  height: 2.75rem;
  font-size: 1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border: none;
  border-radius: 0.5rem;
}

.login-page__submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.4);
}

.login-page__submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-page__loading-icon {
  width: 1.25rem;
  height: 1.25rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.login-page__footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  text-align: center;
}

.login-page__footer p {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

@media (max-width: 640px) {
  .login-page__content { padding: 1.5rem; }
  .login-page__card { padding: 2rem 1.5rem; }
  .login-page__card-title { font-size: 1.5rem; }
}
</style>