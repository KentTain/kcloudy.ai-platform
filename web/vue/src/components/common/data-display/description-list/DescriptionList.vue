<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

export interface DescriptionItem {
  label: string
  value?: string | number | null
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link'
  type?: 'text' | 'badge'
}

interface Props {
  items: DescriptionItem[]
  columns?: 1 | 2 | 3
  bordered?: boolean
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  columns: 2,
  bordered: false,
})

const gridCols = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
}

function getDisplayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  return String(value)
}

function getBadgeVariant(item: DescriptionItem): DescriptionItem['badgeVariant'] {
  return item.badgeVariant || 'default'
}
</script>

<template>
  <div :class="cn('grid gap-3', gridCols[props.columns], props.class)">
    <div
      v-for="(item, index) in items"
      :key="index"
      :class="cn(
        'flex min-w-0 flex-col gap-1',
        props.bordered && 'border-b border-border pb-3'
      )"
    >
      <dt class="text-sm text-muted-foreground">
        {{ item.label }}
      </dt>
      <dd class="text-sm font-medium break-all">
        <slot name="item" :item="item" :index="index">
          <template v-if="item.type === 'badge'">
            <Badge :variant="getBadgeVariant(item)">
              {{ getDisplayValue(item.value) }}
            </Badge>
          </template>
          <template v-else>
            {{ getDisplayValue(item.value) }}
          </template>
        </slot>
      </dd>
    </div>
  </div>
</template>
