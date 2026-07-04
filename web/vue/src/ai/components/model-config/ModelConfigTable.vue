<script setup lang="ts">
/**
 * 模型配置 - 二级树表格
 *
 * 不使用 tanstack-table 的 expandable（与扁平数据冲突），
 * 改为直接用 Vue 模板渲染，展开状态由 expandedPlugins 管理。
 */
import { ref, computed } from "vue";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge, Button } from "@/components";
import { ChevronRight, Settings, Star, Eye } from "lucide-vue-next";
import type {
  PluginWithModels,
  ModelConfigItem,
  ModelTypeKey,
  DefaultModelItem,
} from "@/ai/types/modelConfig";
import { MODEL_TYPE_LABELS } from "@/ai/types/modelConfig";

const props = defineProps<{
  plugins: PluginWithModels[];
  defaultModels: DefaultModelItem[];
}>();

const emit = defineEmits<{
  (e: "configure-models", plugin: PluginWithModels): void;
  (e: "set-default", model: ModelConfigItem, plugin: PluginWithModels): void;
  (e: "view-detail", pluginId: string): void;
}>();

// 展开状态
const expandedPlugins = ref<Set<string>>(new Set());

function toggleExpand(pluginId: string) {
  const s = new Set(expandedPlugins.value);
  if (s.has(pluginId)) {
    s.delete(pluginId);
  } else {
    s.add(pluginId);
  }
  expandedPlugins.value = s;
}

function isExpanded(pluginId: string): boolean {
  return expandedPlugins.value.has(pluginId);
}

// 默认全部展开
function initExpanded() {
  expandedPlugins.value = new Set(props.plugins.map((p) => p.plugin_id));
}

// 首次数据加载时默认展开
import { watch } from "vue";
watch(
  () => props.plugins,
  () => {
    if (expandedPlugins.value.size === 0 && props.plugins.length > 0) {
      initExpanded();
    }
  },
  { immediate: true },
);

// 状态显示
const statusMap: Record<string, { label: string; variant: "default" | "outline" }> = {
  active: { label: "已启动", variant: "default" },
  inactive: { label: "已停止", variant: "outline" },
};
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead class="w-10"></TableHead>
          <TableHead style="width: 200px">编码</TableHead>
          <TableHead style="width: 180px">名称</TableHead>
          <TableHead style="width: 120px">模型类型</TableHead>
          <TableHead style="width: 80px">默认</TableHead>
          <TableHead style="width: 100px">状态</TableHead>
          <TableHead style="width: 200px">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <template v-for="plugin in plugins" :key="plugin.plugin_id">
          <!-- 一级：插件行 -->
          <TableRow
            class="bg-muted/30 cursor-pointer"
            @click="toggleExpand(plugin.plugin_id)"
          >
            <TableCell class="py-2">
              <Button
                variant="ghost"
                size="icon"
                class="h-6 w-6"
                @click.stop="toggleExpand(plugin.plugin_id)"
              >
                <ChevronRight
                  class="h-4 w-4 transition-transform"
                  :style="isExpanded(plugin.plugin_id) ? 'transform: rotate(90deg)' : ''"
                />
              </Button>
            </TableCell>
            <TableCell class="py-2">
              <span class="text-muted-foreground text-xs">{{ plugin.plugin_id }}</span>
            </TableCell>
            <TableCell class="py-2">
              <span class="font-medium">{{ plugin.plugin_name }}</span>
            </TableCell>
            <TableCell class="py-2"></TableCell>
            <TableCell class="py-2"></TableCell>
            <TableCell class="py-2">
              <Badge
                :variant="(statusMap[plugin.status]?.variant ?? 'outline')"
              >
                {{ statusMap[plugin.status]?.label ?? plugin.status }}
              </Badge>
            </TableCell>
            <TableCell class="py-2">
              <div class="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  @click.stop="emit('view-detail', plugin.plugin_id)"
                >
                  <Eye class="mr-1 h-4 w-4" />详情
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  @click.stop="emit('configure-models', plugin)"
                >
                  <Settings class="mr-1 h-4 w-4" />配置模型
                </Button>
              </div>
            </TableCell>
          </TableRow>

          <!-- 二级：模型行 -->
          <template v-if="isExpanded(plugin.plugin_id)">
            <TableRow
              v-for="model in plugin.models"
              :key="`${plugin.plugin_id}-${model.model_name}`"
              class="hover:bg-muted/50"
            >
              <TableCell class="py-2"></TableCell>
              <TableCell class="py-2">
                <span class="text-muted-foreground text-xs pl-6">{{ model.model_name }}</span>
              </TableCell>
              <TableCell class="py-2">
                <span class="pl-6">{{ model.model_label || model.model_name }}</span>
              </TableCell>
              <TableCell class="py-2">
                <Badge variant="outline">
                  {{ MODEL_TYPE_LABELS[model.model_type as ModelTypeKey] || model.model_type }}
                </Badge>
              </TableCell>
              <TableCell class="py-2">
                <Badge v-if="model.is_default" variant="default" class="gap-1">
                  <Star class="h-3 w-3" />默认
                </Badge>
              </TableCell>
              <TableCell class="py-2"></TableCell>
              <TableCell class="py-2">
                <div class="flex items-center gap-1 pl-6">
                  <Button
                    v-if="!model.is_default"
                    variant="ghost"
                    size="sm"
                    @click.stop="emit('set-default', model, plugin)"
                  >
                    <Star class="mr-1 h-4 w-4" />设置默认
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </template>
        </template>

        <!-- 空数据 -->
        <TableRow v-if="plugins.length === 0">
          <TableCell :colspan="7" class="h-24 text-center text-muted-foreground">
            暂无数据
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
