<script setup lang="ts">
import { ref, computed } from 'vue';
import { Button } from '@/components';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, Play, Loader2, Wand2 } from 'lucide-vue-next';
import { notifyError, notifySuccess } from '@/framework/utils/feedback';
import {
  getInstalledSkills,
  invokeSkillStream,
  type PluginDefinition,
} from '@/tenant/api/plugin';

interface Props {
  conversationId: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  invoked: [message: string];
}>();

const installedSkills = ref<PluginDefinition[]>([]);
const selectedSkills = ref<PluginDefinition[]>([]);
const userMessage = ref('');
const invoking = ref(false);
const loadingSkills = ref(false);

const canInvoke = computed(() => {
  return selectedSkills.value.length > 0 && userMessage.value.trim() && !invoking.value;
});

const loadInstalledSkills = async () => {
  loadingSkills.value = true;
  try {
    const res = await getInstalledSkills();
    if (res.code === 200 && res.data) {
      installedSkills.value = res.data;
    }
  } catch (error) {
    notifyError('加载已安装 Skill 失败');
  } finally {
    loadingSkills.value = false;
  }
};

const toggleSkill = (skill: PluginDefinition) => {
  const index = selectedSkills.value.findIndex((s) => s.plugin_id === skill.plugin_id);
  if (index > -1) {
    selectedSkills.value.splice(index, 1);
  } else {
    // 最多选择 5 个 Skill
    if (selectedSkills.value.length < 5) {
      selectedSkills.value.push(skill);
    } else {
      notifyError('最多选择 5 个 Skill');
    }
  }
};

const isSkillSelected = (pluginId: string) => {
  return selectedSkills.value.some((s) => s.plugin_id === pluginId);
};

const handleInvoke = async () => {
  if (!canInvoke.value) return;

  invoking.value = true;
  const fullMessage = ref('');

  await invokeSkillStream(
    {
      conversation_id: props.conversationId,
      skill_ids: selectedSkills.value.map((s) => s.plugin_id),
      user_message: userMessage.value,
    },
    (chunk) => {
      fullMessage.value += chunk;
    },
    (message) => {
      notifySuccess('Skill 调用完成');
      emit('invoked', message || fullMessage.value);
      // 清空状态
      userMessage.value = '';
      selectedSkills.value = [];
      invoking.value = false;
    },
    (error) => {
      notifyError(`调用失败: ${error}`);
      invoking.value = false;
    }
  );
};

loadInstalledSkills();
</script>

<template>
  <div class="flex h-full flex-col border-l bg-background">
    <!-- 头部 -->
    <div class="flex items-center justify-between border-b p-4">
      <h3 class="flex items-center gap-2 font-semibold">
        <Wand2 class="h-4 w-4" />
        调用 Skill
      </h3>
      <Button variant="ghost" size="sm" @click="emit('close')">
        <X class="h-4 w-4" />
      </Button>
    </div>

    <!-- 已选 Skills -->
    <div v-if="selectedSkills.length > 0" class="border-b p-4">
      <div class="mb-2 text-sm font-medium">
        已选择 ({{ selectedSkills.length }}/5)
      </div>
      <div class="flex flex-wrap gap-2">
        <Badge
          v-for="skill in selectedSkills"
          :key="skill.plugin_id"
          variant="default"
          class="cursor-pointer"
          @click="toggleSkill(skill)"
        >
          {{ skill.name || skill.plugin_id }}
          <X class="ml-1 h-3 w-3" />
        </Badge>
      </div>
    </div>

    <!-- Skill 列表 -->
    <ScrollArea class="flex-1 p-4">
      <div v-if="loadingSkills" class="flex justify-center py-8">
        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
      <div v-else-if="installedSkills.length === 0" class="py-8 text-center text-sm text-muted-foreground">
        暂无已安装的 Skill
      </div>
      <div v-else class="space-y-2">
        <div
          v-for="skill in installedSkills"
          :key="skill.plugin_id"
          class="cursor-pointer rounded-lg border p-3 transition-colors hover:bg-accent"
          :class="{ 'border-primary bg-accent': isSkillSelected(skill.plugin_id) }"
          @click="toggleSkill(skill)"
        >
          <div class="font-medium">{{ skill.name || skill.plugin_id }}</div>
          <div class="mt-1 text-xs text-muted-foreground">
            {{ skill.manifest_type || 'skill' }}
          </div>
        </div>
      </div>
    </ScrollArea>

    <!-- 输入区域 -->
    <div class="border-t p-4">
      <Input
        v-model="userMessage"
        placeholder="输入您的请求..."
        class="mb-2"
        :disabled="invoking"
        @keydown.enter="handleInvoke"
      />
      <Button
        class="w-full"
        :disabled="!canInvoke"
        @click="handleInvoke"
      >
        <Loader2 v-if="invoking" class="mr-1 h-4 w-4 animate-spin" />
        <Play v-else class="mr-1 h-4 w-4" />
        {{ invoking ? '执行中...' : '执行' }}
      </Button>
    </div>
  </div>
</template>
