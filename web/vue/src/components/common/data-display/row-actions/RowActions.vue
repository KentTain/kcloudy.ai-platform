<script setup lang="ts">
import { computed } from "vue"
import type { Component } from "vue"
import { Button } from "@/components/common/general/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MoreHorizontal } from "@lucide/vue"

export interface RowAction {
  key: string
  label: string
  icon?: Component
  onClick: () => void
  disabled?: boolean
  variant?: "default" | "destructive"
}

const props = withDefaults(defineProps<{ actions: RowAction[]; maxInline?: number }>(), {
  maxInline: 2,
})

const needDropdown = computed(() => props.actions.length > props.maxInline + 1)

const inlineActions = computed(() => {
  if (!needDropdown.value) return props.actions
  return props.actions.slice(0, props.maxInline)
})

const dropdownActions = computed(() => {
  if (!needDropdown.value) return []
  return props.actions.slice(props.maxInline)
})

const hasDestructiveInDropdown = computed(() => dropdownActions.value.some((a) => a.variant === "destructive"))
const nonDestructiveDropdownActions = computed(() => dropdownActions.value.filter((a) => a.variant !== "destructive"))
const destructiveDropdownActions = computed(() => dropdownActions.value.filter((a) => a.variant === "destructive"))
</script>

<template>
  <div class="flex items-center gap-1">
    <Button
      v-for="action in inlineActions"
      :key="action.key"
      variant="ghost"
      size="sm"
      :disabled="action.disabled"
      :class="action.variant === 'destructive' ? 'text-destructive hover:text-destructive' : ''"
      @click="action.onClick"
    >
      <component :is="action.icon" v-if="action.icon" class="mr-1 h-3.5 w-3.5" />
      {{ action.label }}
    </Button>
    <DropdownMenu v-if="needDropdown">
      <DropdownMenuTrigger as-child>
        <Button variant="ghost" size="sm">
          <MoreHorizontal class="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <template v-if="hasDestructiveInDropdown">
          <DropdownMenuItem
            v-for="action in nonDestructiveDropdownActions"
            :key="action.key"
            :disabled="action.disabled"
            @click="action.onClick"
          >
            <component :is="action.icon" v-if="action.icon" class="mr-2 h-4 w-4" />
            {{ action.label }}
          </DropdownMenuItem>
          <DropdownMenuSeparator v-if="nonDestructiveDropdownActions.length > 0" />
          <DropdownMenuItem
            v-for="action in destructiveDropdownActions"
            :key="action.key"
            :disabled="action.disabled"
            class="text-destructive focus:text-destructive"
            @click="action.onClick"
          >
            <component :is="action.icon" v-if="action.icon" class="mr-2 h-4 w-4" />
            {{ action.label }}
          </DropdownMenuItem>
        </template>
        <template v-else>
          <DropdownMenuItem
            v-for="action in dropdownActions"
            :key="action.key"
            :disabled="action.disabled"
            @click="action.onClick"
          >
            <component :is="action.icon" v-if="action.icon" class="mr-2 h-4 w-4" />
            {{ action.label }}
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>
