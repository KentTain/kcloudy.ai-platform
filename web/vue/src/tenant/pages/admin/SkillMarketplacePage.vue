<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { Search, RefreshCw, Loader2 } from 'lucide-vue-next';
import AppPage from '@/framework/layouts/components/AppPage.vue';
import { Button, Input } from '@/components';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import SkillCard from '@/ai/components/SkillCard.vue';
import SkillPreviewDialog from '@/ai/components/SkillPreviewDialog.vue';
import { notifyError, notifySuccess } from '@/framework/utils/feedback';
import {
  getRemoteSkills,
  syncSkillFromMarketplace,
  getInstalledSkills,
  type RemoteSkillInfo,
  type PluginDefinition,
} from '@/tenant/api/plugin';

const route = useRoute();
const marketplaceId = computed(() => route.params.id as string);

const loading = ref(false);
const syncing = ref(false);
const remoteSkills = ref<RemoteSkillInfo[]>([]);
const installedSkills = ref<PluginDefinition[]>([]);
const searchKeyword = ref('');
const selectedTab = ref<'all' | 'knowledge' | 'script'>('all');
const previewSkillId = ref<string | null>(null);
const previewOpen = ref(false);

const filteredSkills = computed(() => {
  let skills = remoteSkills.value;

  if (selectedTab.value !== 'all') {
    skills = skills.filter((s) => s.skill_type === selectedTab.value);
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    skills = skills.filter(
      (s) =>
        s.name.toLowerCase().includes(keyword) ||
        s.description?.toLowerCase().includes(keyword) ||
        s.tags.some((t) => t.toLowerCase().includes(keyword))
    );
  }

  return skills;
});

const loadRemoteSkills = async () => {
  loading.value = true;
  try {
    const res = await getRemoteSkills(marketplaceId.value, {
      keyword: searchKeyword.value || undefined,
    });
    if (res.code === 200 && res.data) {
      remoteSkills.value = res.data;
    } else {
      notifyError(res.msg || '加载 Skill 列表失败');
    }
  } catch (error) {
    notifyError('加载 Skill 列表失败');
  } finally {
    loading.value = false;
  }
};

const loadInstalledSkills = async () => {
  try {
    const res = await getInstalledSkills();
    if (res.code === 200 && res.data) {
      installedSkills.value = res.data;
    }
  } catch (error) {
    console.error('加载已安装 Skill 失败:', error);
  }
};

const isSkillInstalled = (skillId: string) => {
  return installedSkills.value.some((s) => s.plugin_id === skillId);
};

const handleInstallSkill = async (skillId: string) => {
  syncing.value = true;
  try {
    const res = await syncSkillFromMarketplace(marketplaceId.value, skillId);
    if (res.code === 200) {
      notifySuccess('Skill 安装成功');
      await loadInstalledSkills();
    } else {
      notifyError(res.msg || '安装失败');
    }
  } catch (error) {
    notifyError('安装失败');
  } finally {
    syncing.value = false;
  }
};

const handlePreviewSkill = (skillId: string) => {
  previewSkillId.value = skillId;
  previewOpen.value = true;
};

const handleSearch = () => {
  loadRemoteSkills();
};

onMounted(() => {
  loadRemoteSkills();
  loadInstalledSkills();
});
</script>

<template>
  <AppPage title="Skill 市场" variant="list">
    <template #actions>
      <Button variant="outline" :disabled="loading" @click="loadRemoteSkills">
        <RefreshCw v-if="loading" class="mr-1 h-4 w-4 animate-spin" />
        <RefreshCw v-else class="mr-1 h-4 w-4" />
        刷新
      </Button>
    </template>

    <!-- 搜索和筛选 -->
    <div class="mb-4 flex items-center gap-4">
      <div class="relative flex-1 max-w-md">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          v-model="searchKeyword"
          placeholder="搜索 Skill..."
          class="pl-10"
          @keydown.enter="handleSearch"
        />
      </div>

      <Tabs v-model="selectedTab" @update:model-value="loadRemoteSkills">
        <TabsList>
          <TabsTrigger value="all">全部</TabsTrigger>
          <TabsTrigger value="knowledge">知识文档</TabsTrigger>
          <TabsTrigger value="script">简单脚本</TabsTrigger>
        </TabsList>
      </Tabs>
    </div>

    <!-- Skill 列表 -->
    <div v-if="loading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="i in 6"
        :key="i"
        class="h-48 animate-pulse rounded-lg bg-muted"
      />
    </div>

    <div
      v-else-if="filteredSkills.length > 0"
      class="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
    >
      <SkillCard
        v-for="skill in filteredSkills"
        :key="skill.plugin_id"
        :skill="skill"
        :installed="isSkillInstalled(skill.plugin_id)"
        @install="handleInstallSkill(skill.plugin_id)"
        @preview="handlePreviewSkill(skill.plugin_id)"
      />
    </div>

    <div v-else class="py-12 text-center text-muted-foreground">
      <Loader2 v-if="syncing" class="mx-auto mb-2 h-8 w-8 animate-spin" />
      暂无 Skill 数据
    </div>

    <!-- 预览对话框 -->
    <SkillPreviewDialog
      v-model:open="previewOpen"
      :skill-id="previewSkillId"
    />
  </AppPage>
</template>
