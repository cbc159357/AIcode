<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <aside class="w-96 bg-gray-800/80 border-l border-gray-700 overflow-y-auto flex flex-col">
    <!-- 视频预览 -->
    <div class="p-4 border-b border-gray-700">
      <h3 class="text-sm font-bold text-gray-300 mb-2">预览</h3>
      <div class="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
        <span class="text-gray-600 text-sm">视频预览区</span>
      </div>
    </div>

    <!-- 进度条 -->
    <div v-if="appStore.progressLabel" class="px-4 py-2 border-b border-gray-700">
      <div class="flex justify-between text-xs text-gray-400 mb-1">
        <span>{{ appStore.progressLabel }}</span>
        <span>{{ appStore.progressPercent }}%</span>
      </div>
      <div class="w-full bg-gray-700 rounded-full h-1.5">
        <div
          class="bg-blue-500 h-1.5 rounded-full transition-all"
          :style="{ width: `${appStore.progressPercent}%` }"
        />
      </div>
    </div>

    <!-- 运行日志 -->
    <div class="flex-1 p-4 overflow-y-auto">
      <div class="flex justify-between items-center mb-2">
        <h3 class="text-sm font-bold text-gray-300">运行日志</h3>
        <button
          class="text-xs text-gray-500 hover:text-gray-300"
          @click="appStore.clearLogs()"
        >
          清除
        </button>
      </div>
      <div class="space-y-1 text-xs font-mono">
        <div
          v-for="(entry, i) in appStore.logs"
          :key="i"
          class="py-0.5"
          :class="{
            'text-gray-400': entry.level === 'info',
            'text-green-400': entry.level === 'success',
            'text-yellow-400': entry.level === 'warn',
            'text-red-400': entry.level === 'error',
          }"
        >
          {{ entry.message }}
        </div>
      </div>
    </div>
  </aside>
</template>
