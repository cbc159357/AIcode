<script setup lang="ts">
import type { Shot } from '@/types'

defineProps<{
  shot: Shot
}>()

const emit = defineEmits<{
  edit: [shot: Shot]
  regenerate: [shot: Shot]
}>()
</script>

<template>
  <div class="rounded-lg bg-gray-800/60 border border-gray-700 overflow-hidden hover:border-blue-500/50 transition group">
    <!-- 图片区域 -->
    <div class="aspect-[9/16] bg-gray-900 relative">
      <img
        v-if="shot.imagePath"
        :src="shot.imagePath"
        class="w-full h-full object-cover"
        :alt="`Shot ${shot.index}`"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-600 text-xs">
        待生成
      </div>

      <!-- 序号 -->
      <span class="absolute top-1 left-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
        {{ shot.index + 1 }}
      </span>

      <!-- 操作按钮 -->
      <div class="absolute bottom-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition">
        <button
          class="bg-blue-600/80 text-white text-xs px-2 py-1 rounded hover:bg-blue-600"
          @click="emit('edit', shot)"
        >
          编辑
        </button>
        <button
          class="bg-orange-600/80 text-white text-xs px-2 py-1 rounded hover:bg-orange-600"
          @click="emit('regenerate', shot)"
        >
          重生
        </button>
      </div>
    </div>

    <!-- 旁白文本 -->
    <div class="p-2">
      <p class="text-xs text-gray-300 line-clamp-3">{{ shot.narration || shot.text }}</p>
    </div>
  </div>
</template>
