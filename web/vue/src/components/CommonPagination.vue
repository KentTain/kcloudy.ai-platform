<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from '@lucide/vue'

interface Props {
  total: number
  page?: number
  pageSize?: number
  pageSizeOptions?: number[]
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  page: 1,
  pageSize: 10,
  pageSizeOptions: () => [10, 20, 50, 100],
})

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
}>()

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))

const currentPage = computed({
  get: () => Math.min(props.page, totalPages.value) || 1,
  set: (val: number) => emit('update:page', val),
})

const currentPageSize = computed({
  get: () => props.pageSize,
  set: (val: number) => {
    emit('update:pageSize', val)
    emit('update:page', 1)
  },
})

const pageNumbers = computed(() => {
  const pages: (number | 'ellipsis')[] = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)

    if (current > 3) {
      pages.push('ellipsis')
    }

    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (current < total - 2) {
      pages.push('ellipsis')
    }

    pages.push(total)
  }

  return pages
})

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

function goFirst() {
  goToPage(1)
}

function goPrev() {
  goToPage(currentPage.value - 1)
}

function goNext() {
  goToPage(currentPage.value + 1)
}

function goLast() {
  goToPage(totalPages.value)
}
</script>

<template>
  <div v-if="total > 0" :class="cn('flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between', props.class)">
    <div class="text-sm text-muted-foreground">
      共 <span class="font-medium text-foreground">{{ total }}</span> 条
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          class="h-8 w-8"
          :disabled="currentPage <= 1"
          @click="goFirst"
        >
          <ChevronsLeft class="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          class="h-8 w-8"
          :disabled="currentPage <= 1"
          @click="goPrev"
        >
          <ChevronLeft class="h-4 w-4" />
        </Button>
      </div>

      <div class="flex items-center gap-1">
        <template v-for="(p, i) in pageNumbers" :key="i">
          <span
            v-if="p === 'ellipsis'"
            class="px-2 text-muted-foreground"
          >...</span>
          <Button
            v-else
            :variant="p === currentPage ? 'default' : 'ghost'"
            size="icon"
            class="h-8 w-8"
            @click="goToPage(p)"
          >
            {{ p }}
          </Button>
        </template>
      </div>

      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          class="h-8 w-8"
          :disabled="currentPage >= totalPages"
          @click="goNext"
        >
          <ChevronRight class="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          class="h-8 w-8"
          :disabled="currentPage >= totalPages"
          @click="goLast"
        >
          <ChevronsRight class="h-4 w-4" />
        </Button>
      </div>

      <div class="flex items-center gap-2">
        <Select v-model="currentPageSize">
          <SelectTrigger class="h-8 w-[70px]">
            <SelectValue :placeholder="String(pageSize)" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem
              v-for="size in pageSizeOptions"
              :key="size"
              :value="size"
            >
              {{ size }}
            </SelectItem>
          </SelectContent>
        </Select>
        <span class="text-sm text-muted-foreground">条/页</span>
      </div>
    </div>
  </div>
</template>
