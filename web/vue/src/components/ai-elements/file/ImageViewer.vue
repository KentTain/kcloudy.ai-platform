<!-- src/components/ai-elements/file/ImageViewer.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { ZoomInIcon, ZoomOutIcon, RotateCwIcon } from 'lucide-vue-next'
import { Button } from '@/components'

const props = defineProps<{
  url: string
  zoom?: boolean
  rotate?: boolean
}>()

const scale = ref(1)
const rotation = ref(0)

const zoomIn = () => {
  scale.value = Math.min(3, scale.value + 0.2)
}

const zoomOut = () => {
  scale.value = Math.max(0.5, scale.value - 0.2)
}

const rotateImage = () => {
  rotation.value = (rotation.value + 90) % 360
}
</script>

<template>
  <div data-testid="image-viewer" class="space-y-4">
    <div class="overflow-auto flex items-center justify-center min-h-[400px]">
      <img
        :src="url"
        :style="{
          transform: `scale(${scale}) rotate(${rotation}deg)`,
        }"
        class="max-w-full transition-transform"
      />
    </div>

    <div v-if="zoom || rotate" class="flex items-center justify-center gap-2">
      <Button v-if="zoom" variant="outline" size="sm" @click="zoomOut">
        <ZoomOutIcon class="size-4" />
      </Button>
      <Button v-if="zoom" variant="outline" size="sm" @click="zoomIn">
        <ZoomInIcon class="size-4" />
      </Button>
      <Button v-if="rotate" variant="outline" size="sm" @click="rotateImage">
        <RotateCwIcon class="size-4" />
      </Button>
    </div>
  </div>
</template>
