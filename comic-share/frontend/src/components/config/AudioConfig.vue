<script setup lang="ts">
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
</script>

<template>
  <div class="space-y-3">
    <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">音频设置</h4>

    <a-checkbox v-model="configStore.enableBgm">
      启用背景音乐
    </a-checkbox>

    <a-checkbox v-model="configStore.enableSubtitle">
      启用字幕
    </a-checkbox>
  </div>
</template>
