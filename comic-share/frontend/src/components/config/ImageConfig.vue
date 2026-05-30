<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import { IMAGE_SIZES } from '@/config/constants'
import { listEngines, type EngineItem } from '@/services/workflow'

const configStore = useConfigStore()
const sizeOptions = IMAGE_SIZES.map(s => ({ label: s.label, value: s.value }))

const engineOptions = ref<{ label: string; value: string; disabled?: boolean }[]>([])

async function fetchEngines() {
  try {
    const resp = await listEngines()
    engineOptions.value = resp.engines.map((e: EngineItem) => ({
      label: e.name,
      value: e.id,
      disabled: !e.has_workflow,
    }))
    if (!configStore.activeEngine && resp.default) {
      configStore.activeEngine = resp.default
    }
  } catch {
    engineOptions.value = []
  }
}

onMounted(fetchEngines)
</script>

<template>
  <div class="space-y-3">
    <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">图片设置</h4>

    <div>
      <label class="text-xs text-gray-400 block mb-1">生图引擎</label>
      <a-select
        v-model="configStore.activeEngine"
        :options="engineOptions"
        size="small"
        placeholder="选择引擎"
      />
    </div>

    <div>
      <label class="text-xs text-gray-400 block mb-1">尺寸</label>
      <a-select
        v-model="configStore.imageSize"
        :options="sizeOptions"
        size="small"
        placeholder="选择尺寸"
      />
    </div>
  </div>
</template>
