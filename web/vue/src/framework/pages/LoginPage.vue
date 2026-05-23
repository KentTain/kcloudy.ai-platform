<script setup lang="ts">
/**
 * LoginPage 登录页面
 */
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/iam/stores/auth";
import CommonButton from "@/components/CommonButton.vue";
import CommonInput from "@/components/CommonInput.vue";
import CommonCard from "@/components/CommonCard.vue";

const router = useRouter();
const authStore = useAuthStore();

const username = ref(localStorage.getItem("last_login_account") || "");
const password = ref("");
const loading = ref(false);
const error = ref("");

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = "请输入用户名和密码";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    await authStore.login({
      account: username.value,
      password: password.value,
    });
    localStorage.setItem("last_login_account", username.value);
    router.push("/");
  } catch (err: any) {
    // 处理登录失败
    const message = err?.response?.data?.msg || err?.message || "登录失败，请重试";
    error.value = message;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="login-page">
    <CommonCard class="login-page__card" title="AI 助手平台">
      <form class="login-page__form" @submit.prevent="handleLogin">
        <div class="login-page__field">
          <label class="login-page__label">用户名</label>
          <CommonInput v-model="username" placeholder="请输入用户名" />
        </div>
        <div class="login-page__field">
          <label class="login-page__label">密码</label>
          <CommonInput v-model="password" type="password" placeholder="请输入密码" />
        </div>
        <div v-if="error" class="login-page__error">{{ error }}</div>
        <CommonButton type="submit" :loading="loading" block>
          登录
        </CommonButton>
      </form>
    </CommonCard>
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

.login-page__card {
  width: 400px;
}

.login-page__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-page__field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.login-page__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.login-page__error {
  color: var(--color-danger);
  font-size: 0.875rem;
  text-align: center;
}
</style>
