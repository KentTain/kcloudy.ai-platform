<script setup lang="ts">
/**
 * AdminConsoleLayout 管理后台布局
 */
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";
import { useRouter } from "vue-router";
import { Button } from "@/components/ui/button";
import { Shield, LogOut } from "@lucide/vue";

const adminAuthStore = useAdminAuthStore();
const router = useRouter();

const handleLogout = async () => {
  await adminAuthStore.logout();
  router.push("/admin/login");
};
</script>

<template>
  <div class="admin-layout">
    <header class="admin-layout__header">
      <div class="admin-layout__brand">
        <Shield class="admin-layout__brand-icon" />
        <span class="admin-layout__brand-text">管理后台</span>
      </div>
      <div class="admin-layout__user">
        <span class="admin-layout__username">{{ adminAuthStore.username }}</span>
        <Button variant="ghost" size="sm" @click="handleLogout">
          <LogOut class="w-4 h-4" />
        </Button>
      </div>
    </header>
    <main class="admin-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f5f5f5;
}

.admin-layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 1.5rem;
  background: #1a1a2e;
  color: #fff;
}

.admin-layout__brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.admin-layout__brand-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #dc2626;
}

.admin-layout__brand-text {
  font-size: 1.125rem;
  font-weight: 600;
}

.admin-layout__user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.admin-layout__username {
  font-size: 0.875rem;
  color: #9ca3af;
}

.admin-layout__main {
  flex: 1;
  padding: 1.5rem;
}
</style>
