<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import type { MediaItem } from '@/types'
import { getMediaUrl } from '@/services/archives'

const props = defineProps<{
  media: MediaItem[]
  loading: boolean
  filter: 'all' | 'image' | 'audio' | 'video'
}>()

const filtered = computed(() => {
  if (props.filter === 'all') return props.media
  return props.media.filter(m => m.type === props.filter)
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1048576).toFixed(1)}MB`
}

const typeIconMap: Record<string, string> = {
  image: 'lucide:image',
  audio: 'lucide:music',
  video: 'lucide:film',
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 媒体网格 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <a-spin />
    </div>

    <div v-else-if="filtered.length" class="flex-1 overflow-y-auto p-3">
      <div class="grid grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2">
        <div
          v-for="item in filtered"
          :key="item.path"
          class="rounded-lg bg-gray-900/50 border border-gray-700/50 overflow-hidden group"
        >
          <!-- 图片缩略图 -->
          <div v-if="item.type === 'image'" class="aspect-square bg-gray-800">
            <img
              :src="getMediaUrl(item.path)"
              :alt="item.filename"
              class="w-full h-full object-cover"
              loading="lazy"
            />
          </div>

          <!-- 音频/视频占位 -->
          <div v-else class="aspect-square bg-gray-800 flex items-center justify-center">
            <Icon :icon="typeIconMap[item.type]" class="w-8 h-8 text-gray-500" />
          </div>

          <!-- 文件信息 -->
          <div class="px-2 py-1.5">
            <div class="text-xs text-gray-300 truncate">{{ item.filename }}</div>
            <div class="text-xs text-gray-500">{{ formatSize(item.size) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-500">
      <Icon icon="lucide:inbox" class="w-8 h-8 mb-2 opacity-40" />
      <span class="text-xs">暂无媒体资源</span>
    </div>
  </div>
</template>
