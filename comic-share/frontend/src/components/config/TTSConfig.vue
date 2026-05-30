<script setup lang="ts">
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
</script>

<template>
  <div class="space-y-3">
    <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">TTS 设置</h4>

    <div>
      <label class="text-xs text-gray-400 block mb-1">参考音频</label>
      <a-input
        v-model="configStore.ttsRefAudio"
        size="small"
        placeholder="参考音频名称（待接入列表）"
      />
    </div>

    <div>
      <label class="text-xs text-gray-400 block mb-1">语速</label>
      <a-slider
        v-model="configStore.ttsSpeed"
        :min="0.5"
        :max="2.0"
        :step="0.1"
        show-tooltip
      />
    </div>
  </div>
</template>
