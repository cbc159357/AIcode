<script setup lang="ts">
import { ref, computed } from 'vue'
import { Icon } from '@iconify/vue'
import type { RHWorkflowParam, ParamGroup } from '@/services/runninghub'
import ModelSelector from './ModelSelector.vue'
import { archBadgeClass } from '@/utils/modelArchColors'
import { useModelCompat } from '@/composables/useModelCompat'

const props = defineProps<{
  group: ParamGroup
  params: RHWorkflowParam[]
}>()

const emit = defineEmits<{
  (e: 'update', nodeId: string, fieldName: string, value: string | number | boolean): void
}>()

const collapsed = ref(props.group.defaultCollapsed)

const { dominantBaseModel, isIncompatible } = useModelCompat(computed(() => props.params))

const priorityColor: Record<string, string> = {
  high: 'text-orange-400',
  medium: 'text-blue-400',
  low: 'text-gray-500',
}

/**
 * 模型节点类型排序权重（UNET=0 → VAE=1 → CLIP=2 → 其他=9）
 * 关键词匹配，兼容 UNETLoader / DiffusionModelLoader / CheckpointLoader 等各种命名
 */
function modelSortRank(classType: string): number {
  const c = classType.toLowerCase()
  if (c.includes('unet') || c.includes('diffusion') || c.includes('checkpoint') || c.includes('lora')) return 0
  if (c.includes('vae')) return 1
  if (c.includes('clip')) return 2
  return 9
}

/**
 * 字段内部排序：ComfyUI 节点上→下对应展示左→右
 * name 类字段（模型文件）在前，属性字段（dtype/type/device/strength）在后
 */
function fieldSortRank(fieldName: string): number {
  if (fieldName.includes('name') || fieldName.includes('path') || fieldName.includes('ckpt')) return 0
  return 1
}

/** 按 nodeId 合并，保留首次出现顺序；模型节点按 UNET→VAE→CLIP 排序 */
const nodeGroups = computed(() => {
  const map = new Map<string, RHWorkflowParam[]>()
  for (const p of props.params) {
    if (!map.has(p.nodeId)) map.set(p.nodeId, [])
    map.get(p.nodeId)!.push(p)
  }
  const groups = [...map.entries()].map(([nodeId, ps], idx) => {
    const sorted = [...ps].sort((a, b) => fieldSortRank(a.fieldName) - fieldSortRank(b.fieldName))
    return { nodeId, params: sorted, _idx: idx }
  })
  groups.sort((a, b) => {
    const ra = modelSortRank(nodeClass(a.params[0]))
    const rb = modelSortRank(nodeClass(b.params[0]))
    if (ra !== rb) return ra - rb
    return a._idx - b._idx
  })
  return groups
})

/** 返回节点可读标题：剥离 ComfyUI 自动生成的 "节点44(UNETLoader)" 格式，只保留类名 */
function nodeClass(p: RHWorkflowParam): string {
  const raw = p.nodeTitle ?? p.description.split('.')[0]
  const m = raw.match(/^节点\d+\((.+)\)$/)
  return m ? m[1] : raw
}

/** 多字段节点中，长文本（提示词）独占整行 */
function fieldFullWidth(param: RHWorkflowParam, total: number): boolean {
  return total > 1 && param.type === 'text' && String(param.currentValue).length > 50
}
</script>

<template>
  <div class="border border-gray-700/40 rounded-lg overflow-hidden">
    <!-- 组标题栏 -->
    <button
      class="w-full flex items-center gap-2 px-3 py-2 bg-gray-800/40 hover:bg-gray-700/40 transition-colors"
      @click="collapsed = !collapsed"
    >
      <Icon
        :icon="collapsed ? 'lucide:chevron-right' : 'lucide:chevron-down'"
        class="w-3.5 h-3.5 text-gray-400 shrink-0"
      />
      <span class="text-xs font-bold text-gray-300">{{ group.title }}</span>
      <span class="text-xs text-gray-500 ml-auto">({{ nodeGroups.length }})</span>
    </button>

    <!-- 参数列表（按节点合并，自适应网格） -->
    <div v-if="!collapsed" class="px-3 py-2 space-y-3">
      <div v-for="ng in nodeGroups" :key="ng.nodeId">

        <!-- ① 单字段节点：传统单行（ID + 节点标题 + 字段标签 + 全宽输入） -->
        <div v-if="ng.params.length === 1" class="flex items-center gap-2">
          <div class="text-xs text-sky-300 bg-sky-900/50 border border-sky-700/60 rounded px-1.5 py-0.5 shrink-0 font-mono">
            {{ ng.nodeId }}
          </div>
          <span class="text-xs text-cyan-300 font-medium shrink-0" :title="nodeClass(ng.params[0])">
            {{ nodeClass(ng.params[0]) }}
          </span>
          <!-- 架构标签 -->
          <span
            v-if="ng.params[0].modelMeta"
            class="text-[9px] px-1 py-0.5 rounded border shrink-0 font-mono"
            :class="[
              archBadgeClass(ng.params[0].modelMeta.baseModel),
              isIncompatible(ng.params[0]) ? 'ring-1 ring-red-500/60' : ''
            ]"
          >{{ ng.params[0].modelMeta.baseModel }}</span>
          <span class="text-xs shrink-0 whitespace-nowrap" :class="priorityColor[ng.params[0].priority]">
            {{ ng.params[0].label }}
          </span>
          <!-- 模型选择器 -->
          <ModelSelector
            v-if="ng.params[0].modelMeta"
            :model-value="String(ng.params[0].currentValue)"
            :resource-type="ng.params[0].modelMeta.resourceType"
            :target-base-model="dominantBaseModel"
            :incompatible="isIncompatible(ng.params[0])"
            class="flex-1 min-w-0"
            @update:model-value="emit('update', ng.params[0].nodeId, ng.params[0].fieldName, $event)"
          />
          <a-textarea
            v-else-if="ng.params[0].type === 'text'"
            :model-value="String(ng.params[0].currentValue)"
            :auto-size="{ minRows: 1, maxRows: 4 }"
            size="small"
            class="flex-1 min-w-0"
            @update:model-value="emit('update', ng.params[0].nodeId, ng.params[0].fieldName, $event)"
          />
          <a-input-number
            v-else-if="ng.params[0].type === 'number'"
            :model-value="Number(ng.params[0].currentValue)"
            :min="ng.params[0].constraints.min"
            :max="ng.params[0].constraints.max"
            :step="ng.params[0].constraints.step || 1"
            size="small"
            class="flex-1 min-w-0"
            @update:model-value="emit('update', ng.params[0].nodeId, ng.params[0].fieldName, $event ?? 0)"
          />
          <a-input
            v-else
            :model-value="String(ng.params[0].currentValue)"
            size="small"
            class="flex-1 min-w-0"
            @update:model-value="emit('update', ng.params[0].nodeId, ng.params[0].fieldName, $event)"
          />
        </div>

        <!-- ② 多字段节点：节点头 + 自适应网格 -->
        <template v-else>
          <!-- 节点头：ID + 类名 + 架构标签 -->
          <div class="flex items-center gap-1.5 mb-1.5">
            <div class="text-xs text-sky-300 bg-sky-900/50 border border-sky-700/60 rounded px-1.5 py-0.5 shrink-0 font-mono">
              {{ ng.nodeId }}
            </div>
            <span class="text-xs text-cyan-300 font-medium" :title="nodeClass(ng.params[0])">
              {{ nodeClass(ng.params[0]) }}
            </span>
            <span
              v-if="ng.params.some(p => p.modelMeta)"
              class="text-[9px] px-1 py-0.5 rounded border font-mono"
              :class="archBadgeClass(ng.params.find(p => p.modelMeta)?.modelMeta?.baseModel ?? '')"
            >{{ ng.params.find(p => p.modelMeta)?.modelMeta?.baseModel }}</span>
          </div>

          <!-- 字段网格：auto-fill，每格最小 140px，标签在上输入在下 -->
          <div
            class="grid gap-x-3 gap-y-2 pl-7"
            style="grid-template-columns: repeat(auto-fill, minmax(140px, 1fr))"
          >
            <div
              v-for="param in ng.params"
              :key="param.fieldName"
              :class="fieldFullWidth(param, ng.params.length) ? 'col-span-full' : ''"
            >
              <div class="text-xs mb-0.5 truncate" :class="priorityColor[param.priority]">
                {{ param.label }}
              </div>
              <a-textarea
                v-if="fieldFullWidth(param, ng.params.length)"
                :model-value="String(param.currentValue)"
                :auto-size="{ minRows: 1, maxRows: 4 }"
                size="small"
                class="w-full"
                @update:model-value="emit('update', param.nodeId, param.fieldName, $event)"
              />
              <a-input-number
                v-else-if="param.type === 'number'"
                :model-value="Number(param.currentValue)"
                :min="param.constraints.min"
                :max="param.constraints.max"
                :step="param.constraints.step || 1"
                size="small"
                class="w-full"
                @update:model-value="emit('update', param.nodeId, param.fieldName, $event ?? 0)"
              />
              <!-- 模型字段用 ModelSelector，其余用普通输入 -->
              <ModelSelector
                v-else-if="param.modelMeta"
                :model-value="String(param.currentValue)"
                :resource-type="param.modelMeta.resourceType"
                :target-base-model="dominantBaseModel"
                :incompatible="isIncompatible(param)"
                class="w-full"
                @update:model-value="emit('update', param.nodeId, param.fieldName, $event)"
              />
              <a-input
                v-else
                :model-value="String(param.currentValue)"
                size="small"
                class="w-full"
                @update:model-value="emit('update', param.nodeId, param.fieldName, $event)"
              />
            </div>
          </div>
        </template>

      </div>
    </div>
  </div>
</template>
