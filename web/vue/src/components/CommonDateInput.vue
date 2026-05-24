<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, ref } from 'vue'
import { format, parse, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isToday, addMonths, subMonths, isValid } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ChevronLeft, ChevronRight, Calendar } from '@lucide/vue'

interface Props {
  modelValue?: string | [string, string]
  type?: 'single' | 'range'
  format?: string
  placeholder?: string
  disabled?: boolean
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: undefined,
  type: 'single',
  format: 'yyyy-MM-dd',
  placeholder: '选择日期',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | [string, string] | undefined]
}>()

const open = ref(false)
const currentMonth = ref(new Date())
const rangeStart = ref<Date | null>(null)
const rangeEnd = ref<Date | null>(null)

// 显示文本
const displayText = computed(() => {
  if (!props.modelValue) return ''

  if (props.type === 'single') {
    return props.modelValue as string
  } else {
    const [start, end] = props.modelValue as [string, string]
    if (start && end) {
      return `${start} ~ ${end}`
    }
    return start || ''
  }
})

// 当前月份的日历数据
const calendarDays = computed(() => {
  const start = startOfMonth(currentMonth.value)
  const end = endOfMonth(currentMonth.value)
  const days = eachDayOfInterval({ start, end })

  // 补齐第一天前的空白
  const startDay = start.getDay()
  const paddingDays = Array(startDay).fill(null)

  return [...paddingDays, ...days]
})

// 判断日期是否被选中
function isSelected(date: Date): boolean {
  if (props.type === 'single') {
    if (!props.modelValue) return false
    const selected = parse(props.modelValue as string, props.format, new Date())
    return isValid(selected) && isSameDay(date, selected)
  } else {
    const [start, end] = (props.modelValue as [string, string]) || []
    if (!start) return false
    const startDate = parse(start, props.format, new Date())
    if (!isValid(startDate)) return false

    if (end) {
      const endDate = parse(end, props.format, new Date())
      return isValid(endDate) && isSameDay(date, startDate) || isSameDay(date, endDate)
    }
    return isSameDay(date, startDate)
  }
}

// 判断日期是否在范围内
function isInRange(date: Date): boolean {
  if (props.type !== 'range' || !rangeStart.value || !rangeEnd.value) return false
  return date >= rangeStart.value && date <= rangeEnd.value
}

// 选择日期
function selectDate(date: Date) {
  const formatted = format(date, props.format)

  if (props.type === 'single') {
    emit('update:modelValue', formatted)
    open.value = false
  } else {
    if (!rangeStart.value || rangeEnd.value) {
      // 开始新的选择
      rangeStart.value = date
      rangeEnd.value = null
      emit('update:modelValue', [formatted, ''])
    } else {
      // 完成选择
      if (date < rangeStart.value) {
        rangeEnd.value = rangeStart.value
        rangeStart.value = date
      } else {
        rangeEnd.value = date
      }
      const startFormatted = format(rangeStart.value, props.format)
      const endFormatted = format(rangeEnd.value, props.format)
      emit('update:modelValue', [startFormatted, endFormatted])
      open.value = false
    }
  }
}

// 上一个月
function prevMonth() {
  currentMonth.value = subMonths(currentMonth.value, 1)
}

// 下一个月
function nextMonth() {
  currentMonth.value = addMonths(currentMonth.value, 1)
}

// 清除选择
function clearValue() {
  rangeStart.value = null
  rangeEnd.value = null
  emit('update:modelValue', props.type === 'single' ? undefined : undefined)
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <div :class="cn('relative', props.class)">
        <Input
          :model-value="displayText"
          :placeholder="placeholder"
          :disabled="disabled"
          readonly
          class="cursor-pointer pr-10"
        />
        <Calendar class="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      </div>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-0" align="start">
      <div class="p-3">
        <!-- 月份导航 -->
        <div class="flex items-center justify-between mb-3">
          <Button variant="ghost" size="icon" class="h-7 w-7" @click="prevMonth">
            <ChevronLeft class="h-4 w-4" />
          </Button>
          <span class="text-sm font-medium">
            {{ format(currentMonth, 'yyyy年M月', { locale: zhCN }) }}
          </span>
          <Button variant="ghost" size="icon" class="h-7 w-7" @click="nextMonth">
            <ChevronRight class="h-4 w-4" />
          </Button>
        </div>

        <!-- 星期标题 -->
        <div class="grid grid-cols-7 gap-1 mb-2">
          <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="text-center text-xs text-muted-foreground py-1">
            {{ day }}
          </div>
        </div>

        <!-- 日期格子 -->
        <div class="grid grid-cols-7 gap-1">
          <template v-for="(day, index) in calendarDays" :key="index">
            <div v-if="!day" class="h-8 w-8" />
            <Button
              v-else
              :variant="isSelected(day) ? 'default' : 'ghost'"
              :class="cn(
                'h-8 w-8 p-0 text-sm',
                isToday(day) && 'border border-primary',
                isInRange(day) && 'bg-primary/10'
              )"
              @click="selectDate(day)"
            >
              {{ format(day, 'd') }}
            </Button>
          </template>
        </div>

        <!-- 清除按钮 -->
        <div class="mt-3 flex justify-end">
          <Button variant="ghost" size="sm" @click="clearValue">
            清除
          </Button>
        </div>
      </div>
    </PopoverContent>
  </Popover>
</template>
