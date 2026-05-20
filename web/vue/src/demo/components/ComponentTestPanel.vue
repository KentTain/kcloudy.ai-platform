<!-- src/demo/components/ComponentTestPanel.vue -->
<script setup lang="ts">
import { ref } from "vue";
import AppButton from "@/components/ui/AppButton.vue";
import AppCard from "@/components/ui/AppCard.vue";
import AppLoading from "@/components/ui/AppLoading.vue";
import AppModal from "@/components/ui/AppModal.vue";
import { useModal } from "@/composables/useModal";

// AppButton 测试状态
const clickCount = ref(0);
const buttonVariant = ref<"primary" | "secondary">("primary");
const buttonDisabled = ref(false);

// AppCard 测试状态
const showCardTitle = ref(true);
const cardContentIndex = ref(0);
const cardContents = ["内容 A", "内容 B", "内容 C"];

// AppModal 测试状态
const modal = useModal();
const modalSubmitCount = ref(0);

// AppLoading 测试状态
const loadingSize = ref<"sm" | "md" | "lg">("md");
</script>

<template>
  <div class="space-y-4">
    <!-- AppButton -->
    <AppCard title="AppButton 按钮">
      <div class="space-y-3">
        <div class="flex items-center gap-4">
          <AppButton :variant="buttonVariant" :disabled="buttonDisabled" @click="clickCount++">
            点击我
          </AppButton>
          <AppButton variant="secondary" :disabled="buttonDisabled" @click="clickCount++">
            次要按钮
          </AppButton>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1">
            <input v-model="buttonVariant" type="radio" value="primary" /> primary
          </label>
          <label class="flex items-center gap-1">
            <input v-model="buttonVariant" type="radio" value="secondary" /> secondary
          </label>
          <label class="flex items-center gap-1">
            <input v-model="buttonDisabled" type="checkbox" /> disabled
          </label>
        </div>
        <p class="text-sm text-gray-500">点击次数：{{ clickCount }}</p>
      </div>
    </AppCard>

    <!-- AppCard -->
    <AppCard title="AppCard 卡片">
      <div class="space-y-3">
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1">
            <input v-model="showCardTitle" type="checkbox" /> 显示标题
          </label>
          <AppButton @click="cardContentIndex = (cardContentIndex + 1) % cardContents.length">
            切换内容
          </AppButton>
        </div>
        <div class="rounded-lg border border-dashed border-gray-300 p-4">
          <AppCard :title="showCardTitle ? '卡片标题' : ''">
            <p class="text-sm text-gray-600">{{ cardContents[cardContentIndex] }}</p>
          </AppCard>
        </div>
      </div>
    </AppCard>

    <!-- AppModal -->
    <AppCard title="AppModal 弹窗">
      <div class="space-y-3">
        <AppButton @click="modal.open()">打开弹窗</AppButton>
        <p class="text-sm text-gray-500">弹窗提交次数：{{ modalSubmitCount }}</p>
      </div>
    </AppCard>

    <AppModal :open="modal.isOpen.value" title="测试弹窗" @close="modal.close()">
      <p class="text-sm text-gray-600">这是一个测试弹窗，点击提交会增加计数。</p>
      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" @click="modal.close()">取消</AppButton>
          <AppButton @click="modalSubmitCount++; modal.close()">提交</AppButton>
        </div>
      </template>
    </AppModal>

    <!-- AppLoading -->
    <AppCard title="AppLoading 加载">
      <div class="space-y-3">
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1">
            <input v-model="loadingSize" type="radio" value="sm" /> sm
          </label>
          <label class="flex items-center gap-1">
            <input v-model="loadingSize" type="radio" value="md" /> md
          </label>
          <label class="flex items-center gap-1">
            <input v-model="loadingSize" type="radio" value="lg" /> lg
          </label>
        </div>
        <div class="rounded-lg border border-dashed border-gray-300 p-4">
          <AppLoading :size="loadingSize" />
        </div>
      </div>
    </AppCard>
  </div>
</template>
