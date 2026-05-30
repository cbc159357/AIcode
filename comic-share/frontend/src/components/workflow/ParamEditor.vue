<script setup lang="ts">
import { computed } from 'vue'
import type { RHWorkflowParam, ParamGroup } from '@/services/runninghub'
import ParamGroupComponent from './ParamGroup.vue'

const props = defineProps<{
  params: RHWorkflowParam[]
  paramGroups?: ParamGroup[]
  excludeNodeIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'update', index: number, value: string | number | boolean): void
}>()

const excludedSet = computed(() => new Set(props.excludeNodeIds ?? []))

const visibleParams = computed(() =>
  excludedSet.value.size
    ? props.params.filter(p => !excludedSet.value.has(p.nodeId))
    : props.params,
)

const groupedParamMap = computed(() => {
  const map: Record<string, RHWorkflowParam[]> = {}
  if (!props.paramGroups?.length) return map
  const nodeSet = new Set(props.paramGroups.flatMap(g => g.nodeIds))
  for (const g of props.paramGroups) {
    map[g.groupId] = visibleParams.value.filter(
      p => g.nodeIds.includes(p.nodeId) && nodeSet.has(p.nodeId),
    )
  }
  return map
})

const ungroupedParams = computed(() => {
  if (!props.paramGroups?.length) return visibleParams.value
  const assignedIds = new Set(props.paramGroups.flatMap(g => g.nodeIds))
  return visibleParams.value.filter(p => !assignedIds.has(p.nodeId))
})

function modelSortRank(classType: string): number {
  const c = classType.toLowerCase()
  if (c.includes('unet') || c.includes('diffusion') || c.includes('checkpoint') || c.includes('lora')) return 0
  if (c.includes('vae')) return 1
  if (c.includes('clip')) return 2
  return 9
}

function fieldSortRank(fieldName: string): number {
  if (fieldName.includes('name') || fieldName.includes('path') || fieldName.includes('ckpt')) return 0
  return 1
}

/** 按 nodeId 合并，字段内 name 在前属性在后，节点间 UNET→VAE→CLIP */
function toNodeGroups(list: RHWorkflowParam[]) {
  const map = new Map<string, RHWorkflowParam[]>()
  for (const p of list) {
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
}

const ungroupedNodeGroups = computed(() => toNodeGroups(ungroupedParams.value))
const flatNodeGroups = computed(() => toNodeGroups(visibleParams.value))

function handleGroupUpdate(nodeId: string, fieldName: string, val: string | number | boolean) {
  const idx = props.params.findIndex(p => p.nodeId === nodeId && p.fieldName === fieldName)
  if (idx >= 0) emit('update', idx, val)
}

const priorityColor: Record<string, string> = {
  high: 'text-orange-400',
  medium: 'text-blue-400',
  low: 'text-gray-500',
}

function nodeClass(p: RHWorkflowParam): string {
  const raw = p.nodeTitle ?? p.description.split('.')[0]
  const m = raw.match(/^节点\d+\((.+)\)$/)
  return m ? m[1] : raw
}

function fieldFullWidth(param: RHWorkflowParam, total: number): boolean {
  return total > 1 && param.type === 'text' && String(param.currentValue).length > 50
}
</script>

<template>
  <div class="space-y-2">
    <!-- 分组模式 -->
    <template v-if="paramGroups?.length">
      <ParamGroupComponent
        v-for="group in paramGroups"
        :key="group.groupId"
        :group="group"
        :params="groupedParamMap[group.groupId] ?? []"
        @update="handleGroupUpdate"
      />
      <!-- 未分组的剩余参数（单字段行 / 多字段网格） -->
      <div v-if="ungroupedNodeGroups.length" class="space-y-3 pt-1">
        <div v-for="ng in ungroupedNodeGroups" :key="ng.nodeId">
          <!-- 单字段：传统行 -->
          <div v-if="ng.params.length === 1" class="flex items-center gap-2">
            <div class="text-xs text-sky-300 bg-sky-900/50 border border-sky-700/60 rounded px-1.5 py-0.5 shrink-0 font-mono">{{ ng.nodeId }}</div>
            <span class="text-xs text-cyan-300 font-medium shrink-0" :title="nodeClass(ng.params[0])">{{ nodeClass(ng.params[0]) }}</span>
            <span class="text-xs shrink-0 whitespace-nowrap" :class="priorityColor[ng.params[0].priority]">{{ ng.params[0].label }}</span>
            <a-textarea v-if="ng.params[0].type === 'text'" :model-value="String(ng.params[0].currentValue)" :auto-size="{ minRows: 1, maxRows: 4 }" size="small" class="flex-1 min-w-0" @update:model-value="handleGroupUpdate(ng.params[0].nodeId, ng.params[0].fieldName, $event)" />
            <a-input-number v-else-if="ng.params[0].type === 'number'" :model-value="Number(ng.params[0].currentValue)" :min="ng.params[0].constraints.min" :max="ng.params[0].constraints.max" :step="ng.params[0].constraints.step || 1" size="small" class="flex-1 min-w-0" @update:model-value="handleGroupUpdate(ng.params[0].nodeId, ng.params[0].fieldName, $event ?? 0)" />
            <a-input v-else :model-value="String(ng.params[0].currentValue)" size="small" class="flex-1 min-w-0" @update:model-value="handleGroupUpdate(ng.params[0].nodeId, ng.params[0].fieldName, $event)" />
          </div>
          <!-- 多字段：节点头 + 网格 -->
          <template v-else>
            <div class="flex items-center gap-1.5 mb-1.5">
              <div class="text-xs text-sky-300 bg-sky-900/50 border border-sky-700/60 rounded px-1.5 py-0.5 shrink-0 font-mono">{{ ng.nodeId }}</div>
              <span class="text-xs text-cyan-300 font-medium" :title="nodeClass(ng.params[0])">{{ nodeClass(ng.params[0]) }}</span>
            </div>
            <div class="grid gap-x-3 gap-y-2 pl-7" style="grid-template-columns: repeat(auto-fill, minmax(140px, 1fr))">
              <div v-for="param in ng.params" :key="param.fieldName" :class="fieldFullWidth(param, ng.params.length) ? 'col-span-full' : ''">
                <div class="text-xs mb-0.5 truncate" :class="priorityColor[param.priority]">{{ param.label }}</div>
                <a-textarea v-if="fieldFullWidth(param, ng.params.length)" :model-value="String(param.currentValue)" :auto-size="{ minRows: 1, maxRows: 4 }" size="small" class="w-full" @update:model-value="handleGroupUpdate(param.nodeId, param.fieldName, $event)" />
                <a-input-number v-else-if="param.type === 'number'" :model-value="Number(param.currentValue)" :min="param.constraints.min" :max="param.constraints.max" :step="param.constraints.step || 1" size="small" class="w-full" @update:model-value="handleGroupUpdate(param.nodeId, param.fieldName, $event ?? 0)" />
                <a-input v-else :model-value="String(param.currentValue)" size="small" class="w-full" @update:model-value="handleGroupUpdate(param.nodeId, param.fieldName, $event)" />
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- 平铺模式（向后兼容） -->
    <template v-else>
      <div v-for="ng in flatNodeGroups" :key="ng.nodeId" class="mb-3">
        <!-- 单字段：传统行 -->
        <div v-if="ng.params.length === 1" class="flex items-center gap-2">
          <div class="text-xs text-sky-300 bg-sky-900/50 border border-sky-700/60 rounded px-1.5 py-0.5 shrink-0 font-mono">{{ ng.nodeId }}</div>
          <span class="text-xs text-cyan-300 font-medium shrink-0" :title="nodeClass(ng.params[0])">{{ nodeClass(ng.params[0]) }}</span>
          <span class="text-xs shrink-0 whitespace-nowrap" :class="priorityColor[ng.params[0].priority]">{{ ng.params[0].label }}</span>
          <a-textarea v-if="ng.params[0].type === 'text'" :model-value="String(ng.params[0].currentValue)" :auto-size="{ minRows: 1, maxRows: 4 }" size="small" class="flex-1 min-w-0" @update:model-value="handleGroupUpdate(ng.params[0].nodeId, ng.params[0].fieldName, $event)" />
          <a-input-number v-else-if="ng.params[0].type === 'number'" :model-value="Number(ng.params[0].currentValue)" :min="ng.params[0].constraints.min" :max="ng.params[0].constraints.max" :step="ng.params[0].constraints.step || 1" size="small" class="flex-1 min-w-0" @update:model-value="handleGroupUpdate(ng.params[0].nodeId, ng.params[0].fieldName, $event ?? 0)" />
          <a-input v-else :model-value="String(ng.params[0].currentValue)" size="small" class="flex-1 min-w-0" @update:model-value="handleGroupUpdate(ng.params[0].nodeId, ng.params[0].fieldName, $event)" />
        </div>
        <!-- 多字段：节点头 + 网格 -->
        <template v-else>
          <div class="flex items-center gap-1.5 mb-1.5">
            <div class="text-xs text-sky-300 bg-sky-900/50 border border-sky-700/60 rounded px-1.5 py-0.5 shrink-0 font-mono">{{ ng.nodeId }}</div>
            <span class="text-xs text-cyan-300 font-medium" :title="nodeClass(ng.params[0])">{{ nodeClass(ng.params[0]) }}</span>
          </div>
          <div class="grid gap-x-3 gap-y-2 pl-7" style="grid-template-columns: repeat(auto-fill, minmax(140px, 1fr))">
            <div v-for="param in ng.params" :key="param.fieldName" :class="fieldFullWidth(param, ng.params.length) ? 'col-span-full' : ''">
              <div class="text-xs mb-0.5 truncate" :class="priorityColor[param.priority]">{{ param.label }}</div>
              <a-textarea v-if="fieldFullWidth(param, ng.params.length)" :model-value="String(param.currentValue)" :auto-size="{ minRows: 1, maxRows: 4 }" size="small" class="w-full" @update:model-value="handleGroupUpdate(param.nodeId, param.fieldName, $event)" />
              <a-input-number v-else-if="param.type === 'number'" :model-value="Number(param.currentValue)" :min="param.constraints.min" :max="param.constraints.max" :step="param.constraints.step || 1" size="small" class="w-full" @update:model-value="handleGroupUpdate(param.nodeId, param.fieldName, $event ?? 0)" />
              <a-input v-else :model-value="String(param.currentValue)" size="small" class="w-full" @update:model-value="handleGroupUpdate(param.nodeId, param.fieldName, $event)" />
            </div>
          </div>
        </template>
      </div>
    </template>

    <div v-if="!visibleParams.length" class="text-xs text-gray-500 text-center py-4">
      暂无可调参数
    </div>
  </div>
</template>
