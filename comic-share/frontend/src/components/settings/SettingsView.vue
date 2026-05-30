<script setup lang="ts">
import { ref, type Component } from 'vue'
import { Icon } from '@iconify/vue'
import LLMConfig from '@/components/config/LLMConfig.vue'
import StyleConfig from '@/components/config/StyleConfig.vue'
import ImageConfig from '@/components/config/ImageConfig.vue'
import TTSConfig from '@/components/config/TTSConfig.vue'
import AudioConfig from '@/components/config/AudioConfig.vue'
import RHConfigCard from '@/components/workflow/RHConfigCard.vue'

interface SettingsCard {
  key: string
  label: string
  icon: string
  component: Component
}

const cards = ref<SettingsCard[]>([
  { key: 'rh', label: 'RunningHub', icon: 'lucide:cloud', component: RHConfigCard },
  { key: 'llm', label: 'LLM 配置', icon: 'lucide:brain', component: LLMConfig },
  { key: 'style', label: '风格配置', icon: 'lucide:palette', component: StyleConfig },
  { key: 'image', label: '生图配置', icon: 'lucide:image', component: ImageConfig },
  { key: 'tts', label: 'TTS 配置', icon: 'lucide:mic', component: TTSConfig },
  { key: 'audio', label: '音频配置', icon: 'lucide:music', component: AudioConfig },
])

const dragIdx = ref(-1)
const dropIdx = ref(-1)

function handleDragStart(idx: number) {
  dragIdx.value = idx
}

function handleDragOver(e: DragEvent, idx: number) {
  e.preventDefault()
  dropIdx.value = idx
}

function handleDrop(idx: number) {
  if (dragIdx.value < 0 || dragIdx.value === idx) return
  const moved = cards.value.splice(dragIdx.value, 1)[0]
  cards.value.splice(idx, 0, moved)
  dragIdx.value = -1
  dropIdx.value = -1
}

function handleDragEnd() {
  dragIdx.value = -1
  dropIdx.value = -1
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <h1 class="text-lg font-bold text-white mb-6">设置</h1>

    <!-- 左右两列布局 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="(card, idx) in cards"
        :key="card.key"
        draggable="true"
        class="rounded-lg bg-gray-800/60 border p-4 transition-all cursor-grab active:cursor-grabbing"
        :class="[
          dropIdx === idx && dragIdx !== idx
            ? 'border-blue-500/60 ring-1 ring-blue-500/30'
            : 'border-gray-700',
          dragIdx === idx ? 'opacity-40' : '',
        ]"
        @dragstart="handleDragStart(idx)"
        @dragover="handleDragOver($event, idx)"
        @drop="handleDrop(idx)"
        @dragend="handleDragEnd"
      >
        <div class="flex items-center gap-2 mb-3">
          <Icon icon="lucide:grip-vertical" class="w-4 h-4 text-gray-600 shrink-0" />
          <Icon :icon="card.icon" class="w-4 h-4 text-blue-400 shrink-0" />
          <h2 class="text-sm font-bold text-gray-300">{{ card.label }}</h2>
        </div>
        <component :is="card.component" />
      </div>
    </div>
  </div>
</template>
