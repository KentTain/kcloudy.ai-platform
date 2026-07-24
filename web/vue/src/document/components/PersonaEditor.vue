<script setup lang="ts">
/**
 * 人设编辑器组件
 */

import { ref, watch } from "vue";
import { Textarea, Input } from "@/components";

const props = defineProps<{
  name?: string;
  instruction?: string;
  description?: string;
}>();

const emit = defineEmits<{
  "update:name": [value: string];
  "update:instruction": [value: string];
  "update:description": [value: string];
}>();

const localName = ref(props.name ?? "");
const localInstruction = ref(props.instruction ?? "");
const localDescription = ref(props.description ?? "");

watch(localName, (v) => emit("update:name", v));
watch(localInstruction, (v) => emit("update:instruction", v));
watch(localDescription, (v) => emit("update:description", v));
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1">
      <label class="text-sm font-medium">名称</label>
      <Input v-model="localName" placeholder="输入人设名称" />
    </div>
    <div class="flex flex-col gap-1">
      <label class="text-sm font-medium">指令</label>
      <Textarea
        v-model="localInstruction"
        placeholder="输入人设指令内容"
        :rows="8"
        class="font-mono text-sm"
      />
    </div>
    <div class="flex flex-col gap-1">
      <label class="text-sm font-medium">描述</label>
      <Input v-model="localDescription" placeholder="输入人设描述（可选）" />
    </div>
  </div>
</template>
