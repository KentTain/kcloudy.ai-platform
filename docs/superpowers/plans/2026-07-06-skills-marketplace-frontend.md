# Skills 市场前端集成实现计划（Phase 7）

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现前端 Skill 市场浏览、Skill 调用面板和聊天界面集成，复用现有插件市场组件，扩展支持 Skill 类型。

**架构：** 新增 Skill 市场浏览页面（复用 RemotePluginBrowsePage 模式），新增 Skill 卡片组件展示 Skill 信息，新增 Skill 调用面板集成到聊天界面。扩展现有 plugin.ts API 支持 Skill 调用和预览。

**技术栈：** Vue 3.5 + TypeScript 5.8 + shadcn-vue + Tailwind CSS + TanStack Table + Vitest

**设计规格：** `docs/superpowers/specs/2026-07-06-skills-marketplace-design.md`（第 7 章）

**前置依赖：** 计划 1（后端基础）和计划 2（运行时与 LangChain 集成）已完成。

---

## 文件结构

### 创建的文件

| 文件路径 | 职责 |
|---------|------|
| `web/vue/src/tenant/pages/admin/SkillMarketplacePage.vue` | Skill 市场浏览页面 |
| `web/vue/src/ai/components/SkillCard.vue` | Skill 卡片组件 |
| `web/vue/src/ai/components/SkillPreviewDialog.vue` | Skill 预览对话框 |
| `web/vue/src/ai/components/SkillInvocationPanel.vue` | Skill 调用面板 |
| `web/vue/src/components/chat/ChatWithSkill.vue` | 带 Skill 的聊天界面 |
| `web/vue/tests/ai/unit/components/test_skill_card.vue.ts` | Skill 卡片单元测试 |

### 修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `web/vue/src/tenant/api/plugin.ts` | 新增 Skill 相关 API 函数和类型 |
| `web/vue/src/tenant/router/index.ts` | 注册 Skill 市场路由 |
| `web/vue/src/ai/router/index.ts` | 注册 Skill 调用页面路由 |

---

## 任务 1：扩展 plugin.ts API 支持 Skill

**文件：**
- 修改：`web/vue/src/tenant/api/plugin.ts`
- 测试：无（API 扩展，由组件测试覆盖）

- [ ] **步骤 1：在 plugin.ts 中新增 Skill 类型定义**

在 `web/vue/src/tenant/api/plugin.ts` 文件末尾新增 Skill 相关类型和 API 函数：

```typescript
// ==================== Skill 相关类型 ====================

export interface RemoteSkillInfo {
  plugin_id: string;
  name: string;
  description: string | null;
  version: string;
  author: string;
  plugin_type: 'skill';
  skill_type: 'knowledge' | 'script';
  tags: string[];
  downloads: number | null;
  icon: string | null;
  download_url: string;
}

export interface SkillListResponse {
  skills: RemoteSkillInfo[];
  total: number;
}

export interface SkillPreviewResponse {
  skill_id: string;
  name: string;
  description: string | null;
  skill_type: 'knowledge' | 'script';
  documents: Record<string, string>;
}

// ==================== Skill API 函数 ====================

/**
 * 获取远程 Skill 列表
 */
export async function getRemoteSkills(
  marketplaceId: string,
  params?: {
    keyword?: string;
    skill_type?: 'knowledge' | 'script';
    page?: number;
    page_size?: number;
  }
): Promise<ApiResponse<SkillListResponse>> {
  const query = new URLSearchParams();
  if (params?.keyword) query.set('keyword', params.keyword);
  if (params?.skill_type) query.set('skill_type', params.skill_type);
  if (params?.page) query.set('page', String(params.page));
  if (params?.page_size) query.set('page_size', String(params.page_size));
  return rawGet(`/tenant/admin/v1/marketplaces/${marketplaceId}/skills?${query.toString()}`);
}

/**
 * 从市场同步 Skill
 */
export async function syncSkillFromMarketplace(
  marketplaceId: string,
  skillId: string
): Promise<ApiResponse<PluginDefinition>> {
  return rawPost(`/tenant/admin/v1/marketplaces/${marketplaceId}/skills/${encodeURIComponent(skillId)}/sync`);
}

/**
 * 获取已安装的 Skills
 */
export async function getInstalledSkills(): Promise<ApiResponse<PluginDefinition[]>> {
  return rawGet('/tenant/admin/v1/plugins?plugin_type=skill');
}

/**
 * 预览 Skill 文档
 */
export async function previewSkill(
  skillId: string
): Promise<ApiResponse<SkillPreviewResponse>> {
  return rawGet(`/ai/console/v1/skills/${encodeURIComponent(skillId)}/preview`);
}

/**
 * 调用 Skill（流式）
 */
export async function invokeSkillStream(
  request: {
    conversation_id: string;
    skill_ids: string[];
    user_message: string;
  },
  onChunk: (chunk: string) => void,
  onComplete: (fullMessage: string) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch('/ai/console/v1/skills/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      onError(`HTTP ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError('无法读取响应流');
      return;
    }

    const decoder = new TextDecoder();
    let fullMessage = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'chunk' && data.content) {
            fullMessage += data.content;
            onChunk(data.content);
          } else if (data.type === 'complete') {
            onComplete(fullMessage || data.message || '');
          } else if (data.type === 'error') {
            onError(data.error || '调用失败');
          }
        } catch (e) {
          // 忽略解析错误的行
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : '网络错误');
  }
}
```

- [ ] **步骤 2：验证 API 文件语法正确**

运行：`cd web/vue && pnpm check 2>&1 | head -20`

预期：无类型错误（如有错误，根据提示修正）

- [ ] **步骤 3：Commit**

```bash
cd web/vue
git add src/tenant/api/plugin.ts
git commit -m "feat(tenant): 扩展 plugin.ts API 支持 Skill

新增 RemoteSkillInfo 类型、getRemoteSkills、syncSkillFromMarketplace、
getInstalledSkills、previewSkill、invokeSkillStream 等 API 函数

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2：实现 Skill 卡片组件

**文件：**
- 创建：`web/vue/src/ai/components/SkillCard.vue`
- 测试：`web/vue/tests/ai/unit/components/test_skill_card.vue.ts`

- [ ] **步骤 1：编写失败的测试**

创建 `web/vue/tests/ai/unit/components/test_skill_card.vue.ts`：

```typescript
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import SkillCard from '@/ai/components/SkillCard.vue';
import type { RemoteSkillInfo } from '@/tenant/api/plugin';

describe('SkillCard', () => {
  const mockSkill: RemoteSkillInfo = {
    plugin_id: 'community/airtable',
    name: 'airtable',
    description: 'Airtable REST API via curl',
    version: '1.1.0',
    author: 'community',
    plugin_type: 'skill',
    skill_type: 'knowledge',
    tags: ['Airtable', 'Productivity'],
    downloads: 100,
    icon: null,
    download_url: 'https://example.com/download',
  };

  it('renders skill name and author', () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: false,
      },
    });

    expect(wrapper.text()).toContain('airtable');
    expect(wrapper.text()).toContain('community');
  });

  it('renders knowledge type label', () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: false,
      },
    });

    expect(wrapper.text()).toContain('知识文档');
  });

  it('renders script type label', () => {
    const scriptSkill = { ...mockSkill, skill_type: 'script' as const };
    const wrapper = mount(SkillCard, {
      props: {
        skill: scriptSkill,
        installed: false,
      },
    });

    expect(wrapper.text()).toContain('简单脚本');
  });

  it('shows install button when not installed', () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: false,
      },
    });

    expect(wrapper.text()).toContain('安装');
  });

  it('shows installed state when installed', () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: true,
      },
    });

    expect(wrapper.text()).toContain('已安装');
  });

  it('emits install event when install button clicked', async () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: false,
      },
    });

    await wrapper.find('[data-testid="install-button"]').trigger('click');
    expect(wrapper.emitted('install')).toBeTruthy();
  });

  it('emits preview event when preview button clicked', async () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: false,
      },
    });

    await wrapper.find('[data-testid="preview-button"]').trigger('click');
    expect(wrapper.emitted('preview')).toBeTruthy();
  });

  it('renders tags', () => {
    const wrapper = mount(SkillCard, {
      props: {
        skill: mockSkill,
        installed: false,
      },
    });

    expect(wrapper.text()).toContain('Airtable');
    expect(wrapper.text()).toContain('Productivity');
  });
});
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd web/vue && pnpm test:unit tests/ai/unit/components/test_skill_card.vue.ts --run`

预期：FAIL，组件不存在

- [ ] **步骤 3：实现 SkillCard 组件**

创建 `web/vue/src/ai/components/SkillCard.vue`：

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components';
import { Badge } from '@/components/ui/badge';
import { Download, Eye, FileText, Code, Check } from '@lucide/vue';
import type { RemoteSkillInfo } from '@/tenant/api/plugin';

interface Props {
  skill: RemoteSkillInfo;
  installed: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  install: [];
  preview: [];
}>();

const skillTypeLabel = computed(() => {
  return props.skill.skill_type === 'knowledge' ? '知识文档' : '简单脚本';
});

const skillTypeIcon = computed(() => {
  return props.skill.skill_type === 'knowledge' ? FileText : Code;
});

const skillTypeColor = computed(() => {
  return props.skill.skill_type === 'knowledge'
    ? 'bg-blue-500'
    : 'bg-green-500';
});

const formatDownloads = (num: number | null): string => {
  if (!num) return '0';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};
</script>

<template>
  <Card class="flex flex-col">
    <CardHeader class="pb-3">
      <div class="flex items-start justify-between">
        <CardTitle class="text-lg">{{ skill.name }}</CardTitle>
        <Badge :class="skillTypeColor">
          <component :is="skillTypeIcon" class="mr-1 h-3 w-3" />
          {{ skillTypeLabel }}
        </Badge>
      </div>
      <div class="text-sm text-muted-foreground">
        by {{ skill.author }}
      </div>
    </CardHeader>

    <CardContent class="flex-1">
      <p class="mb-3 line-clamp-2 text-sm text-muted-foreground">
        {{ skill.description }}
      </p>

      <!-- 标签 -->
      <div class="mb-4 flex flex-wrap gap-1">
        <Badge
          v-for="tag in skill.tags.slice(0, 3)"
          :key="tag"
          variant="outline"
          class="text-xs"
        >
          {{ tag }}
        </Badge>
      </div>

      <!-- 统计信息 -->
      <div class="mb-4 flex items-center gap-4 text-xs text-muted-foreground">
        <span v-if="skill.downloads">
          <Download class="mr-1 inline h-3 w-3" />
          {{ formatDownloads(skill.downloads) }} 次下载
        </span>
        <span>v{{ skill.version }}</span>
      </div>

      <!-- 操作按钮 -->
      <div class="flex gap-2">
        <Button
          v-if="!installed"
          size="sm"
          class="flex-1"
          data-testid="install-button"
          @click="emit('install')"
        >
          <Download class="mr-1 h-3 w-3" />
          安装
        </Button>
        <Button
          v-else
          size="sm"
          variant="outline"
          class="flex-1"
          disabled
        >
          <Check class="mr-1 h-3 w-3" />
          已安装
        </Button>

        <Button
          size="sm"
          variant="ghost"
          data-testid="preview-button"
          @click="emit('preview')"
        >
          <Eye class="mr-1 h-3 w-3" />
          预览
        </Button>
      </div>
    </CardContent>
  </Card>
</template>
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd web/vue && pnpm test:unit tests/ai/unit/components/test_skill_card.vue.ts --run`

预期：8 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd web/vue
git add src/ai/components/SkillCard.vue tests/ai/unit/components/test_skill_card.vue.ts
git commit -m "feat(ai): 实现 SkillCard 卡片组件

展示 Skill 名称、类型、标签、统计信息，支持安装和预览操作

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3：实现 Skill 预览对话框

**文件：**
- 创建：`web/vue/src/ai/components/SkillPreviewDialog.vue`
- 测试：无（由集成测试覆盖）

- [ ] **步骤 1：实现 SkillPreviewDialog 组件**

创建 `web/vue/src/ai/components/SkillPreviewDialog.vue`：

```vue
<script setup lang="ts">
import { ref, watch } from 'vue';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, FileText } from '@lucide/vue';
import { previewSkill, type SkillPreviewResponse } from '@/tenant/api/plugin';
import { notifyError } from '@/framework/utils/feedback';

interface Props {
  skillId: string | null;
  open: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:open': [value: boolean];
}>();

const loading = ref(false);
const skillData = ref<SkillPreviewResponse | null>(null);

const loadSkillPreview = async (skillId: string) => {
  loading.value = true;
  skillData.value = null;
  try {
    const res = await previewSkill(skillId);
    if (res.code === 200 && res.data) {
      skillData.value = res.data;
    } else {
      notifyError(res.msg || '加载 Skill 预览失败');
    }
  } catch (error) {
    notifyError('加载 Skill 预览失败');
  } finally {
    loading.value = false;
  }
};

watch(
  () => [props.skillId, props.open],
  ([skillId, isOpen]) => {
    if (skillId && isOpen) {
      loadSkillPreview(skillId as string);
    }
  },
  { immediate: true }
);
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-3xl max-h-[80vh]">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <FileText class="h-5 w-5" />
          <span v-if="skillData">{{ skillData.name }}</span>
          <span v-else>Skill 预览</span>
          <Badge v-if="skillData" variant="outline">
            {{ skillData.skill_type === 'knowledge' ? '知识文档' : '简单脚本' }}
          </Badge>
        </DialogTitle>
      </DialogHeader>

      <div v-if="loading" class="flex items-center justify-center py-12">
        <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
      </div>

      <ScrollArea v-else-if="skillData" class="h-[60vh] pr-4">
        <div class="space-y-6">
          <!-- 描述 -->
          <div v-if="skillData.description">
            <h3 class="mb-2 font-semibold">描述</h3>
            <p class="text-sm text-muted-foreground">
              {{ skillData.description }}
            </p>
          </div>

          <!-- 文档列表 -->
          <div>
            <h3 class="mb-2 font-semibold">文档内容</h3>
            <div class="space-y-4">
              <div
                v-for="(content, filename) in skillData.documents"
                :key="filename"
                class="rounded-lg border p-4"
              >
                <div class="mb-2 flex items-center gap-2">
                  <FileText class="h-4 w-4 text-muted-foreground" />
                  <span class="font-mono text-sm">{{ filename }}</span>
                </div>
                <pre class="whitespace-pre-wrap text-sm">{{ content }}</pre>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>

      <div v-else class="py-12 text-center text-muted-foreground">
        暂无内容
      </div>
    </DialogContent>
  </Dialog>
</template>
```

- [ ] **步骤 2：验证组件语法正确**

运行：`cd web/vue && pnpm check 2>&1 | head -20`

预期：无类型错误

- [ ] **步骤 3：Commit**

```bash
cd web/vue
git add src/ai/components/SkillPreviewDialog.vue
git commit -m "feat(ai): 实现 SkillPreviewDialog 预览对话框

展示 Skill 文档内容，支持 Markdown 文件预览

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4：实现 Skill 市场浏览页面

**文件：**
- 创建：`web/vue/src/tenant/pages/admin/SkillMarketplacePage.vue`
- 测试：无（由 E2E 测试覆盖）

- [ ] **步骤 1：实现 Skill 市场浏览页面**

创建 `web/vue/src/tenant/pages/admin/SkillMarketplacePage.vue`：

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { Search, RefreshCw, Loader2 } from '@lucide/vue';
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
      skill_type: selectedTab.value === 'all' ? undefined : selectedTab.value,
    });
    if (res.code === 200 && res.data) {
      remoteSkills.value = res.data.skills;
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
```

- [ ] **步骤 2：验证页面语法正确**

运行：`cd web/vue && pnpm check 2>&1 | head -20`

预期：无类型错误

- [ ] **步骤 3：Commit**

```bash
cd web/vue
git add src/tenant/pages/admin/SkillMarketplacePage.vue
git commit -m "feat(tenant): 实现 Skill 市场浏览页面

支持 Skill 列表浏览、搜索、类型筛选、安装和预览

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 5：实现 Skill 调用面板

**文件：**
- 创建：`web/vue/src/ai/components/SkillInvocationPanel.vue`
- 测试：无（由集成测试覆盖）

- [ ] **步骤 1：实现 Skill 调用面板组件**

创建 `web/vue/src/ai/components/SkillInvocationPanel.vue`：

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';
import { Button } from '@/components';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, Play, Loader2, Wand2 } from '@lucide/vue';
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
  const index = selectedSkills.value.findIndex((s) => s.id === skill.id);
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

const isSkillSelected = (skillId: string) => {
  return selectedSkills.value.some((s) => s.id === skillId);
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
          :key="skill.id"
          variant="default"
          class="cursor-pointer"
          @click="toggleSkill(skill)"
        >
          {{ skill.plugin_id }}
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
          :key="skill.id"
          class="cursor-pointer rounded-lg border p-3 transition-colors hover:bg-accent"
          :class="{ 'border-primary bg-accent': isSkillSelected(skill.id) }"
          @click="toggleSkill(skill)"
        >
          <div class="font-medium">{{ skill.plugin_id }}</div>
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
```

- [ ] **步骤 2：验证组件语法正确**

运行：`cd web/vue && pnpm check 2>&1 | head -20`

预期：无类型错误

- [ ] **步骤 3：Commit**

```bash
cd web/vue
git add src/ai/components/SkillInvocationPanel.vue
git commit -m "feat(ai): 实现 SkillInvocationPanel 调用面板

支持选择已安装 Skill（最多 5 个）、输入请求、流式调用

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 6：实现带 Skill 的聊天界面

**文件：**
- 创建：`web/vue/src/components/chat/ChatWithSkill.vue`
- 测试：无（由 E2E 测试覆盖）

- [ ] **步骤 1：实现聊天界面组件**

创建 `web/vue/src/components/chat/ChatWithSkill.vue`：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Button } from '@/components';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Wand2, Send, Loader2 } from '@lucide/vue';
import SkillInvocationPanel from '@/ai/components/SkillInvocationPanel.vue';
import { notifyError } from '@/framework/utils/feedback';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  skill_ids?: string[];
}

interface Props {
  conversationId: string;
}

const props = defineProps<Props>();

const messages = ref<Message[]>([]);
const inputMessage = ref('');
const sending = ref(false);
const showSkillPanel = ref(false);

const handleSend = async () => {
  if (!inputMessage.value.trim() || sending.value) return;

  const userMessage = inputMessage.value;
  inputMessage.value = '';

  // 添加用户消息
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: userMessage,
  });

  sending.value = true;

  // 添加助手消息占位
  const assistantMessage: Message = {
    id: (Date.now() + 1).toString(),
    role: 'assistant',
    content: '',
  };
  messages.value.push(assistantMessage);

  // 调用普通对话 API（非 Skill）
  try {
    const response = await fetch('/ai/console/v1/chat-messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: props.conversationId,
        message: userMessage,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      assistantMessage.content = data.data?.content || data.data?.message || '响应为空';
    } else {
      assistantMessage.content = '请求失败';
      notifyError('发送消息失败');
    }
  } catch (error) {
    assistantMessage.content = '网络错误';
    notifyError('网络错误');
  } finally {
    sending.value = false;
  }
};

const handleSkillInvoked = (message: string) => {
  // 添加 Skill 调用结果为助手消息
  messages.value.push({
    id: Date.now().toString(),
    role: 'assistant',
    content: message,
    skill_ids: [],
  });
  showSkillPanel.value = false;
};
</script>

<template>
  <div class="flex h-full">
    <!-- 主聊天区域 -->
    <div class="flex flex-1 flex-col">
      <!-- 消息列表 -->
      <ScrollArea class="flex-1 p-4">
        <div class="space-y-4">
          <div
            v-for="message in messages"
            :key="message.id"
            class="flex"
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[80%] rounded-lg p-3"
              :class="
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              "
            >
              <p class="whitespace-pre-wrap text-sm">{{ message.content }}</p>
            </div>
          </div>
          <div v-if="sending" class="flex justify-start">
            <div class="rounded-lg bg-muted p-3">
              <Loader2 class="h-4 w-4 animate-spin" />
            </div>
          </div>
        </div>
      </ScrollArea>

      <!-- 输入区域 -->
      <div class="border-t p-4">
        <div class="mb-2 flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            :class="{ 'bg-accent': showSkillPanel }"
            @click="showSkillPanel = !showSkillPanel"
          >
            <Wand2 class="mr-1 h-4 w-4" />
            Skills
          </Button>
        </div>

        <div class="flex gap-2">
          <Input
            v-model="inputMessage"
            placeholder="输入消息或使用 Skill..."
            :disabled="sending"
            @keydown.enter="handleSend"
          />
          <Button :disabled="!inputMessage.trim() || sending" @click="handleSend">
            <Send class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>

    <!-- Skill 调用面板 -->
    <div v-if="showSkillPanel" class="w-96">
      <SkillInvocationPanel
        :conversation-id="conversationId"
        @invoked="handleSkillInvoked"
        @close="showSkillPanel = false"
      />
    </div>
  </div>
</template>
```

- [ ] **步骤 2：验证组件语法正确**

运行：`cd web/vue && pnpm check 2>&1 | head -20`

预期：无类型错误

- [ ] **步骤 3：Commit**

```bash
cd web/vue
git add src/components/chat/ChatWithSkill.vue
git commit -m "feat(components): 实现 ChatWithSkill 聊天界面

集成 Skill 调用面板，支持普通对话和 Skill 调用两种模式

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 7：注册前端路由

**文件：**
- 修改：`web/vue/src/tenant/router/index.ts`
- 修改：`web/vue/src/ai/router/index.ts`
- 测试：无（路由配置，由 E2E 测试覆盖）

- [ ] **步骤 1：在 tenant 路由中注册 Skill 市场页面**

查看 `web/vue/src/tenant/router/index.ts` 现有路由结构，在插件市场相关路由后新增 Skill 市场路由：

```typescript
// 在现有插件市场路由后新增
{
  path: '/admin/marketplaces/:id/skills',
  name: 'SkillMarketplace',
  component: () => import('@/tenant/pages/admin/SkillMarketplacePage.vue'),
  meta: {
    title: 'Skill 市场',
    requiresAuth: true,
    requiresAdmin: true,
  },
},
```

- [ ] **步骤 2：在 ai 路由中注册 Skill 聊天页面**

查看 `web/vue/src/ai/router/index.ts` 现有路由结构，新增 Skill 聊天路由：

```typescript
// 在现有路由后新增
{
  path: '/skills/chat/:conversationId',
  name: 'SkillChat',
  component: () => import('@/components/chat/ChatWithSkill.vue'),
  meta: {
    title: 'Skill 对话',
    requiresAuth: true,
  },
},
```

- [ ] **步骤 3：验证路由配置正确**

运行：`cd web/vue && pnpm check 2>&1 | head -20`

预期：无类型错误

- [ ] **步骤 4：运行前端单元测试确认无回归**

运行：`cd web/vue && pnpm test:unit --run 2>&1 | tail -20`

预期：现有测试全部通过

- [ ] **步骤 5：Commit**

```bash
cd web/vue
git add src/tenant/router/index.ts src/ai/router/index.ts
git commit -m "feat(web): 注册 Skill 市场和 Skill 聊天页面路由

新增 /admin/marketplaces/:id/skills 和 /skills/chat/:conversationId 路由

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 自检

### 规格覆盖度

对照设计规格 `docs/superpowers/specs/2026-07-06-skills-marketplace-design.md` 第 7 章检查：

| 规格章节 | 覆盖任务 | 状态 |
|---------|---------|------|
| 7.1 前端架构扩展 | 任务 1-7 | ✅ |
| 7.2 Skill 市场浏览页面 | 任务 4 | ✅ |
| 7.3 Skill 卡片组件 | 任务 2 | ✅ |
| 7.4 Skill 调用面板 | 任务 5 | ✅ |
| 7.5 集成到聊天界面 | 任务 6 | ✅ |
| 7.6 API 扩展 | 任务 1 | ✅ |

**补充覆盖：**
- Skill 预览对话框（任务 3，规格 7.2 中提到）
- 路由注册（任务 7）

### 占位符扫描

✅ 无"待定"、"TODO"、"后续实现"占位符
✅ 所有代码步骤包含完整代码
✅ 所有测试步骤包含实际测试代码
✅ 无"类似任务 N"引用

### 类型一致性

- `RemoteSkillInfo` 在任务 1 定义，任务 2、4 一致使用
- `PluginDefinition` 复用现有类型，任务 1、4、5 一致使用
- `skill_type` 枚举值 `knowledge | script` 前后端一致
- API 路径 `/tenant/admin/v1/marketplaces/:id/skills` 和 `/ai/console/v1/skills/invoke` 与后端计划一致
- SkillCard 组件 `emit('install')` 和 `emit('preview')` 事件在任务 2 定义，任务 4 一致使用
- SkillInvocationPanel 组件 `emit('invoked')` 和 `emit('close')` 事件在任务 5 定义，任务 6 一致使用

### 修复记录

无需修复，计划与规格一致。

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-07-06-skills-marketplace-frontend.md`。

**本计划覆盖范围：** Phase 7（前端集成），共 7 个任务，实现 Skill 市场浏览、调用面板和聊天界面集成。

**前置依赖：** 计划 1（后端基础）和计划 2（运行时与 LangChain 集成）已完成。

**完整计划系列：**
- 计划 1：后端基础（Phase 1-3）✅ 已完成
- 计划 2：运行时与 LangChain 集成（Phase 4-6）✅ 已完成
- 计划 3：前端集成（Phase 7）✅ 本计划

**两种执行方式：**

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**
