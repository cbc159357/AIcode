/**
 * 配置状态 — LLM/TTS/ComfyUI 设置。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfigStore = defineStore('config', () => {
  // LLM 设置
  const llmProvider = ref('ollama')
  const llmModel = ref('')
  const llmApiKey = ref('')
  const llmTemperature = ref(0.7)
  const llmMaxTokens = ref(4096)

  // 风格/时代
  const stylePreset = ref('anime')
  const eraPreset = ref('modern')

  // 图片设置
  const imageSize = ref('720x1280')
  const activeEngine = ref('runninghub')  // 引擎模式: runninghub | comfyui_local | direct_api

  // TTS 设置
  const ttsRefAudio = ref('')
  const ttsSpeed = ref(1.0)

  // 音频设置
  const enableBgm = ref(true)
  const enableSubtitle = ref(true)

  // 模式切换
  const lowVramMode = ref(false)
  const editMode = ref(false)

  function setLLM(provider: string, model: string, apiKey?: string) {
    llmProvider.value = provider
    llmModel.value = model
    if (apiKey !== undefined) llmApiKey.value = apiKey
  }

  function $reset() {
    llmProvider.value = 'ollama'
    llmModel.value = ''
    llmApiKey.value = ''
    llmTemperature.value = 0.7
    llmMaxTokens.value = 4096
    stylePreset.value = 'anime'
    eraPreset.value = 'modern'
    imageSize.value = '720x1280'
    activeEngine.value = 'runninghub'
    ttsRefAudio.value = ''
    ttsSpeed.value = 1.0
    enableBgm.value = true
    enableSubtitle.value = true
    lowVramMode.value = false
    editMode.value = false
  }

  return {
    llmProvider,
    llmModel,
    llmApiKey,
    llmTemperature,
    llmMaxTokens,
    stylePreset,
    eraPreset,
    imageSize,
    activeEngine,
    ttsRefAudio,
    ttsSpeed,
    enableBgm,
    enableSubtitle,
    lowVramMode,
    editMode,
    setLLM,
    $reset,
  }
})
