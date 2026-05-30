<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import ModelSelector from './ModelSelector.vue'
import type { RHWorkflowParam, ModelSearchResult } from '@/services/runninghub'
import { archBadgeClass } from '@/utils/modelArchColors'

defineProps<{
  groupName: string
  params: RHWorkflowParam[]
}>()

const emit = defineEmits<{
  (e: 'replace', nodeId: string, fieldName: string, value: string, meta?: ModelSearchResult): void
}>()

const openSelector = ref<string | null>(null)  // `${nodeId}::${fieldName}` 或 null

function archClass(baseModel?: string) { return archBadgeClass(baseModel) }

function paramKey(p: RHWorkflowParam) {
  return `${p.nodeId}::${p.fieldName}`
}

function handleSelect(param: RHWorkflowParam, result: ModelSearchResult) {
  emit('replace', param.nodeId, param.fieldName, result.filename, result)
  openSelector.value = null
}
</script>

<template>
  <div class="rounded-lg border border-gray-700 bg-gray-800/40 overflow-hidden">
    <!-- 组标题 -->
    <div class="flex items-center gap-2 px-3 py-2 bg-gray-800/60 border-b border-gray-700">
      <Icon icon="lucide:layers" class="w-3.5 h-3.5 text-blue-400 shrink-0" />
      <span class="text-xs font-bold text-gray-200">{{ groupName }}</span>
      <span class="ml-auto text-xs text-gray-500">{{ params.length }} 个模型槽</span>
    </div>

    <!-- 参数列表 -->
    <div class="divide-y divide-gray-700/50">
      <div
        v-for="param in params"
        :key="paramKey(param)"
        class="px-3 py-2.5 space-y-1.5"
      >
        <!-- 标签 + 架构 -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400 truncate max-w-[90px]">{{ param.label }}</span>
          <span
            v-if="param.modelMeta?.baseModel"
            class="text-[10px] px-1.5 py-0.5 rounded border font-mono"
            :class="archClass(param.modelMeta.baseModel)"
          >
            {{ param.modelMeta.baseModel }}
          </span>
          <span v-else class="text-[10px] text-gray-600">无元数据</span>
        </div>

        <!-- 当前值 + 替换按钮 -->
        <div class="flex items-center gap-2">
          <span class="flex-1 text-xs text-gray-300 font-mono truncate bg-gray-900/60 px-2 py-1 rounded">
            {{ param.currentValue || '(未设置)' }}
          </span>
          <a-button
            size="mini"
            @click="openSelector = openSelector === paramKey(param) ? null : paramKey(param)"
          >
            <template #icon><Icon icon="lucide:replace" class="w-3 h-3" /></template>
            替换
          </a-button>
        </div>

        <!-- 替换选择器（展开） -->
        <div v-if="openSelector === paramKey(param)" class="mt-1">
          <ModelSelector
            :model-value="String(param.currentValue)"
            :resource-type="param.modelMeta?.resourceType ?? ''"
            :target-base-model="param.modelMeta?.baseModel"
            @select="(r: ModelSearchResult) => handleSelect(param, r)"
          />
        </div>
      </div>

      <div v-if="!params.length" class="px-3 py-4 text-xs text-gray-500 text-center">
        该组内无模型参数
      </div>
    </div>
  </div>
</template>
