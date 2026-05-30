<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

const props = defineProps<{
  text: string
  streaming: boolean
}>()

const containerRef = ref<HTMLDivElement>()

watch(() => props.text, async () => {
  if (props.streaming) {
    await nextTick()
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  }
})
</script>

<template>
  <div
    ref="containerRef"
    class="flex-1 overflow-y-auto p-4 font-mono text-sm leading-relaxed text-gray-200 whitespace-pre-wrap"
  >
    <template v-if="text">
      {{ text }}
      <span v-if="streaming" class="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-0.5" />
    </template>
    <template v-else>
      <p class="text-gray-500 italic">等待生成...</p>
    </template>
  </div>
</template>
