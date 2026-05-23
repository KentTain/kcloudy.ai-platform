<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePermissionStore } from '@/iam/stores/permission'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

const permissionStore = usePermissionStore()

const activeResource = ref('')

const loadPermissions = async () => {
  await permissionStore.fetchPermissionGroups()
  if (permissionStore.permissionGroups.length > 0 && !activeResource.value) {
    activeResource.value = permissionStore.permissionGroups[0].resource
  }
}

onMounted(() => {
  loadPermissions()
})
</script>

<template>
  <AppPage title="权限管理" variant="list">
    <Tabs v-model="activeResource">
      <TabsList>
        <TabsTrigger
          v-for="group in permissionStore.permissionGroups"
          :key="group.resource"
          :value="group.resource"
        >
          {{ group.resource }}
        </TabsTrigger>
      </TabsList>

      <TabsContent
        v-for="group in permissionStore.permissionGroups"
        :key="group.resource"
        :value="group.resource"
      >
        <div class="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-[150px]">权限编码</TableHead>
                <TableHead class="w-[120px]">权限名称</TableHead>
                <TableHead class="w-[100px]">资源</TableHead>
                <TableHead class="w-[80px]">操作</TableHead>
                <TableHead class="w-[200px]">描述</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="perm in group.permissions" :key="perm.id">
                <TableCell class="font-medium">{{ perm.code }}</TableCell>
                <TableCell>{{ perm.name }}</TableCell>
                <TableCell>{{ perm.resource }}</TableCell>
                <TableCell>{{ perm.action }}</TableCell>
                <TableCell>{{ perm.description || '--' }}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </TabsContent>
    </Tabs>
  </AppPage>
</template>