<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import type { RadioGroupItemEmits, RadioGroupItemProps } from "reka-ui";
import { CircleIcon } from "lucide-vue-next";
import { reactiveOmit } from "@vueuse/core";
import { RadioGroupIndicator, RadioGroupItem, useForwardPropsEmits } from "reka-ui";
import { cn } from "@/lib/utils";

const props = defineProps<RadioGroupItemProps & { class?: HTMLAttributes["class"] }>();
const emits = defineEmits<RadioGroupItemEmits>();

const delegatedProps = reactiveOmit(props, "class");
const forwarded = useForwardPropsEmits(delegatedProps, emits);
</script>

<template>
  <RadioGroupItem
    data-slot="radio-group-item"
    v-bind="forwarded"
    :class="
      cn(
        'border-input text-primary focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive aspect-square size-4 rounded-full border shadow-xs transition-colors outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
      )
    "
  >
    <RadioGroupIndicator
      data-slot="radio-group-indicator"
      class="flex items-center justify-center"
    >
      <CircleIcon class="fill-primary size-2.5" />
    </RadioGroupIndicator>
  </RadioGroupItem>
</template>
