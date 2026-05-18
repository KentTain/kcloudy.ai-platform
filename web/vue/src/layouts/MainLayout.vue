<script setup lang="ts">
interface Props {
  title?: string;
}

withDefaults(defineProps<Props>(), {
  title: "Demo",
});
</script>

<template>
  <div class="flex min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 border-r border-gray-200 bg-white">
      <div class="flex h-16 items-center justify-center border-b border-gray-200">
        <h1 class="text-xl font-semibold text-gray-800">{{ title }}</h1>
      </div>
      <nav class="p-4">
        <ul class="space-y-2">
          <li>
            <RouterLink
              to="/"
              class="block rounded-lg px-4 py-2 text-gray-700 hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-600"
            >
              首页
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/datasets"
              class="block rounded-lg px-4 py-2 text-gray-700 hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-600"
            >
              知识库
            </RouterLink>
          </li>
        </ul>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>
