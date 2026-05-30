<script setup lang="ts">
import { useConfigStore } from '@/stores/config'
import { STYLE_PRESETS, ERA_PRESETS } from '@/config/constants'

const configStore = useConfigStore()

const styleOptions = STYLE_PRESETS.map(s => ({ label: s.label, value: s.value }))
const eraOptions = ERA_PRESETS.map(e => ({ label: e.label, value: e.value }))
</script>

<template>
  <div class="space-y-3">
    <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">风格设置</h4>

    <div>
      <label class="text-xs text-gray-400 block mb-1">画风</label>
      <a-select
        v-model="configStore.stylePreset"
        :options="styleOptions"
        size="small"
        placeholder="选择画风"
      />
    </div>

    <div>
      <label class="text-xs text-gray-400 block mb-1">时代背景</label>
      <a-select
        v-model="configStore.eraPreset"
        :options="eraOptions"
        size="small"
        placeholder="选择时代"
      />
    </div>
  </div>
</template>
