<script setup lang="ts">
import type { AcceptableValue } from "reka-ui";
import type { HTMLAttributes } from "vue";

import { Dialog, DialogContent, DialogTitle } from "@/components";
import { Command } from "@/components/ui/command";
import { cn } from "@/lib/utils";

interface Props {
  class?: HTMLAttributes["class"];
  title?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: "Model Selector",
});
const value = defineModel<AcceptableValue | AcceptableValue[]>();
</script>

<template>
  <DialogContent :class="cn('p-0', props.class)" v-bind="$attrs">
    <DialogTitle class="sr-only">
      {{ props.title }}
    </DialogTitle>
    <Command class="**:data-[slot=command-input-wrapper]:h-auto" v-model="value">
      <slot />
    </Command>
  </DialogContent>
</template>
