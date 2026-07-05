<script setup lang="ts">
interface Props {
  content: {
    headers: string[]
    rows: any[][]
  }
}
defineProps<Props>()
</script>

<template>
  <div class="overflow-x-auto rounded-lg border">
    <table class="w-full text-sm">
      <thead class="bg-muted/50">
        <tr>
          <th
            v-for="(header, index) in content.headers"
            :key="index"
            class="px-4 py-2 text-left font-medium"
          >
            {{ header }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y">
        <tr
          v-for="(row, rowIndex) in content.rows"
          :key="rowIndex"
          class="hover:bg-muted/30"
        >
          <td
            v-for="(cell, cellIndex) in row"
            :key="cellIndex"
            class="px-4 py-2"
          >
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
