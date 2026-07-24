<script setup lang="ts">
/**
 * 权限管理标签页
 */

import PermissionConfig from "../../../components/PermissionConfig.vue";

defineProps<{
  libraryId: string;
}>();
</script>

<template>
  <PermissionConfig :library-id="libraryId" />
</template>
