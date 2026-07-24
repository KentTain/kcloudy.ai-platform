<script setup lang="ts">
/**
 * 权限配置组件
 */

import { onMounted, ref, watch } from "vue";
import { getRoles, getResourceAcls } from "../../api/permission";
import { getErrorMessage, notifyError } from "@/framework/utils/feedback";
import { Badge } from "@/components";
import type { LibraryRole, ResourceAcl } from "../../types";

const props = defineProps<{
  libraryId: string;
}>();

const roles = ref<LibraryRole[]>([]);
const acls = ref<ResourceAcl[]>([]);
const loading = ref(false);

const fetchData = async () => {
  loading.value = true;
  try {
    const [rolesRes, aclsRes] = await Promise.all([
      getRoles(props.libraryId, { page: 1, page_size: 100 }),
      getResourceAcls(props.libraryId, { page: 1, page_size: 100 }),
    ]);
    roles.value = Array.isArray(rolesRes.data) ? rolesRes.data : [];
    acls.value = Array.isArray(aclsRes.data) ? aclsRes.data : [];
  } catch (error) {
    notifyError(getErrorMessage(error, "获取权限配置失败"));
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});

watch(() => props.libraryId, () => {
  fetchData();
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <div v-if="loading" class="text-sm text-muted-foreground">加载中...</div>
    <template v-else>
      <div>
        <h3 class="mb-2 text-sm font-medium">角色列表</h3>
        <div class="flex flex-wrap gap-2">
          <Badge v-for="role in roles" :key="role.id" variant="secondary">
            {{ role.name }}
          </Badge>
          <span v-if="roles.length === 0" class="text-sm text-muted-foreground">暂无角色</span>
        </div>
      </div>

      <div>
        <h3 class="mb-2 text-sm font-medium">资源 ACL</h3>
        <div v-if="acls.length === 0" class="text-sm text-muted-foreground">暂无 ACL 规则</div>
        <div v-else class="flex flex-col gap-1">
          <div
            v-for="acl in acls"
            :key="acl.id"
            class="flex items-center gap-2 rounded border px-3 py-2 text-sm"
          >
            <span>{{ acl.subject_type }}:{{ acl.subject_id }}</span>
            <span class="text-muted-foreground">-</span>
            <span>{{ acl.action }}</span>
            <Badge :variant="acl.effect === 'allow' ? 'default' : 'destructive'" class="ml-auto">
              {{ acl.effect }}
            </Badge>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
