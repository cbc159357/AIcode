<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <header class="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
    <!-- Logo & 标题 -->
    <div class="flex items-center gap-3">
      <span class="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
        comic-share
      </span>
      <span class="text-xs text-gray-500">AI漫画短片生成器</span>
    </div>

    <!-- 右侧：服务状态 + 预览按钮 -->
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2 text-xs">
        <span class="text-gray-400">ComfyUI</span>
        <span
          class="w-2 h-2 rounded-full"
          :class="appStore.serviceStatus.comfyui === 'connected' ? 'bg-green-400' : 'bg-red-400'"
        />
      </div>
      <div class="flex items-center gap-2 text-xs">
        <span class="text-gray-400">CosyVoice</span>
        <span
          class="w-2 h-2 rounded-full"
          :class="appStore.serviceStatus.cosyvoice === 'connected' ? 'bg-green-400' : 'bg-red-400'"
        />
      </div>

      <!-- 预览抽屉切换按钮 -->
      <button
        title="预览 & 日志"
        class="p-1.5 rounded-md transition"
        :class="appStore.previewDrawerOpen ? 'text-blue-400 bg-blue-600/20' : 'text-gray-400 hover:text-white'"
        @click="appStore.previewDrawerOpen = !appStore.previewDrawerOpen"
      >
        <Icon icon="lucide:panel-right-open" class="w-5 h-5" />
      </button>
    </div>
  </header>
</template>
