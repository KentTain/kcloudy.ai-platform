<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import { Input } from '@/components'

interface Props {
  content: {
    headers: string[]
    rows: any[][]
  }
}

const props = defineProps<Props>()

const searchQuery = ref('')
const sortColumn = ref('')
const sortDirection = ref<'asc' | 'desc'>('asc')

const filteredRows = computed(() => {
  let rows = props.content.rows

  // 搜索筛选
  if (searchQuery.value) {
    rows = rows.filter(row =>
      row.some(cell =>
        String(cell).toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    )
  }

  // 排序
  if (sortColumn.value) {
    const colIndex = props.content.headers.indexOf(sortColumn.value)
    rows = [...rows].sort((a, b) => {
      const aVal = a[colIndex]
      const bVal = b[colIndex]
      const compare = aVal > bVal ? 1 : -1
      return sortDirection.value === 'asc' ? compare : -compare
    })
  }

  return rows
})

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}
</script>

<template>
  <div class="overflow-x-auto rounded-lg border">
    <!-- 筛选栏 -->
    <div class="border-b px-4 py-2">
      <Input
        v-model="searchQuery"
        placeholder="搜索..."
        class="max-w-xs"
      />
    </div>

    <table class="w-full text-sm">
      <thead class="bg-muted/50">
        <tr>
          <th
            v-for="(header, index) in content.headers"
            :key="index"
            class="px-4 py-2 text-left font-medium cursor-pointer hover:bg-muted transition-colors"
            @click="sortBy(header)"
          >
            <div class="flex items-center gap-1">
              {{ header }}
              <ChevronDownIcon
                v-if="sortColumn === header"
                class="size-4 transition-transform"
                :class="{ 'rotate-180': sortDirection === 'desc' }"
              />
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y">
        <tr
          v-for="(row, rowIndex) in filteredRows"
          :key="rowIndex"
          class="hover:bg-muted/30 transition-colors"
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
