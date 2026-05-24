<script setup lang="ts">
import type { TreeComponentNode, TreeAction } from '@/framework/types/tree'
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import CommonTree from '@/components/CommonTree.vue'

interface Props {
  data: TreeComponentNode[]
  actions?: TreeAction[]
  defaultExpandLevel?: number
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  actions: () => [],
  defaultExpandLevel: 1,
})

function handleNodeClick({ node: _node }: { node: TreeComponentNode; level: number }) {
  // 列表树节点点击，不做特殊处理
}

function getVisibleActions(node: TreeComponentNode): TreeAction[] {
  return props.actions.filter(action => {
    if (action.visible) {
      return action.visible(node)
    }
    return true
  })
}
</script>

<template>
  <div :class="cn('flex flex-col gap-1', props.class)">
    <CommonTree
      :data="data"
      :default-expand-level="defaultExpandLevel"
      @node-click="handleNodeClick"
    >
      <template #node="{ node }">
        <div class="flex items-center justify-between gap-2 flex-1">
          <span class="text-sm">{{ node.name }}</span>
          <div v-if="getVisibleActions(node).length" class="flex items-center gap-1">
            <button
              v-for="action in getVisibleActions(node)"
              :key="action.key"
              type="button"
              class="flex h-6 items-center gap-1 rounded px-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
              @click.stop="action.handler(node)"
            >
              <component :is="action.icon" v-if="action.icon" class="h-3 w-3" />
              {{ action.label }}
            </button>
          </div>
        </div>
      </template>
    </CommonTree>
  </div>
</template>