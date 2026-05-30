<script setup lang="ts">
import { ref } from 'vue'
import LLMConfig from '@/components/config/LLMConfig.vue'
import StyleConfig from '@/components/config/StyleConfig.vue'
import ImageConfig from '@/components/config/ImageConfig.vue'
import TTSConfig from '@/components/config/TTSConfig.vue'
import AudioConfig from '@/components/config/AudioConfig.vue'

const storyText = defineModel<string>('storyText', { default: '' })
const emit = defineEmits<{
  runStep: [step: number]
}>()

const activeConfigTab = ref<'llm' | 'style' | 'image' | 'tts' | 'audio'>('llm')

defineProps<{
  currentStep: number
  stepStatuses: Record<number, 'idle' | 'running' | 'done' | 'error'>
}>()

const configTabs = [
  { key: 'llm', label: 'LLM' },
  { key: 'style', label: '风格' },
  { key: 'image', label: '生图' },
  { key: 'tts', label: 'TTS' },
  { key: 'audio', label: '音频' },
] as const
</script>

<template>
  <aside class="w-80 bg-gray-800/80 border-r border-gray-700 overflow-y-auto p-4 flex flex-col gap-4">
    <!-- 故事输入 -->
    <div class="rounded-lg bg-gray-900/50 p-4">
      <h3 class="text-sm font-bold text-gray-300 mb-2">故事输入</h3>
      <a-textarea
        v-model="storyText"
        :auto-size="{ minRows: 5, maxRows: 10 }"
        placeholder="输入你的故事文本..."
      />
    </div>

    <!-- 流程控制 -->
    <div class="rounded-lg bg-gray-900/50 p-4">
      <h3 class="text-sm font-bold text-gray-300 mb-3">流程控制</h3>
      <div class="flex flex-col gap-2">
        <a-button
          v-for="step in 4"
          :key="step"
          :disabled="stepStatuses[step] === 'running' || (step > 1 && stepStatuses[step - 1] !== 'done')"
          :loading="stepStatuses[step] === 'running'"
          :type="stepStatuses[step] === 'done' ? 'outline' : 'primary'"
          :status="stepStatuses[step] === 'done' ? 'success' : stepStatuses[step] === 'error' ? 'danger' : undefined"
          long
          @click="emit('runStep', step)"
        >
          {{ stepStatuses[step] === 'done' ? '✓ ' : '' }}步骤{{ step }}:
          {{ step === 1 ? '生成剧本' : step === 2 ? '生成图片' : step === 3 ? '语音合成' : '视频合成' }}
        </a-button>
      </div>
    </div>

    <!-- 配置面板 -->
    <div class="rounded-lg bg-gray-900/50 p-4">
      <a-radio-group v-model="activeConfigTab" type="button" size="small" class="mb-3 w-full">
        <a-radio v-for="tab in configTabs" :key="tab.key" :value="tab.key">{{ tab.label }}</a-radio>
      </a-radio-group>

      <LLMConfig v-show="activeConfigTab === 'llm'" />
      <StyleConfig v-show="activeConfigTab === 'style'" />
      <ImageConfig v-show="activeConfigTab === 'image'" />
      <TTSConfig v-show="activeConfigTab === 'tts'" />
      <AudioConfig v-show="activeConfigTab === 'audio'" />
    </div>
  </aside>
</template>
