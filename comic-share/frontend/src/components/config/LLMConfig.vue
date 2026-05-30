<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import { fetchModels } from '@/services/llm'
import type { LLMModel } from '@/services/llm'

const configStore = useConfigStore()

const providers = [
  { label: 'Ollama', value: 'ollama' },
  { label: 'LM Studio', value: 'lmstudio' },
  { label: 'vLLM', value: 'vllm' },
  { label: 'Remote-vLLM', value: 'remote-vllm' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '自定义', value: 'custom' },
]

const models = ref<LLMModel[]>([])
const loadingModels = ref(false)

const modelOptions = ref<Array<{ label: string; value: string }>>([])

async function loadModels() {
  loadingModels.value = true
  try {
    models.value = await fetchModels(configStore.llmProvider)
    modelOptions.value = models.value.map(m => ({ label: m.name, value: m.id }))
    if (models.value.length && !configStore.llmModel) {
      configStore.llmModel = models.value[0].id
    }
  } catch {
    models.value = []
    modelOptions.value = []
  } finally {
    loadingModels.value = false
  }
}

watch(() => configStore.llmProvider, loadModels)
onMounted(loadModels)
</script>

<template>
  <div class="space-y-3">
    <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">LLM 设置</h4>

    <div>
      <label class="text-xs text-gray-400 block mb-1">Provider</label>
      <a-select
        v-model="configStore.llmProvider"
        :options="providers"
        size="small"
        placeholder="选择 Provider"
      />
    </div>

    <div>
      <label class="text-xs text-gray-400 block mb-1">模型</label>
      <a-select
        v-model="configStore.llmModel"
        :options="modelOptions"
        :loading="loadingModels"
        size="small"
        placeholder="选择模型"
        allow-search
      />
    </div>

    <div v-if="configStore.llmProvider === 'deepseek' || configStore.llmProvider === 'custom'">
      <label class="text-xs text-gray-400 block mb-1">API Key</label>
      <a-input-password
        v-model="configStore.llmApiKey"
        size="small"
        placeholder="sk-..."
      />
    </div>

    <div>
      <label class="text-xs text-gray-400 block mb-1">Temperature</label>
      <a-slider
        v-model="configStore.llmTemperature"
        :min="0"
        :max="2"
        :step="0.1"
        show-tooltip
      />
    </div>
  </div>
</template>
