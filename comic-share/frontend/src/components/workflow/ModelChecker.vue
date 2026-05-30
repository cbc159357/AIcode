<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { Message } from '@arco-design/web-vue'
import {
  listSavedWorkflows, getSavedWorkflow, applyModelOverrides,
  type RHWorkflowItem, type RHWorkflowDetail, type RHWorkflowParam,
  type ModelSearchResult,
} from '@/services/runninghub'
import ModelGroupItem from './ModelGroupItem.vue'
import { useModelCompat } from '@/composables/useModelCompat'

const workflows = ref<RHWorkflowItem[]>([])
const selectedId = ref<string>('')
const detail = ref<RHWorkflowDetail | null>(null)
const loading = ref(false)
const saving = ref(false)

/** 本次会话中用户做的替换：key = `${nodeId}::${fieldName}` */
const overrides = ref<Map<string, { value: string; meta?: ModelSearchResult }>>(new Map())

async function loadWorkflows() {
  try {
    const r = await listSavedWorkflows()
    workflows.value = r.items
    if (r.items.length && !selectedId.value) selectedId.value = r.items[0].workflowId
    if (selectedId.value) await loadDetail()
  } catch { /* ignore */ }
}

async function loadDetail() {
  if (!selectedId.value) return
  loading.value = true
  overrides.value.clear()
  try {
    const r = await getSavedWorkflow(selectedId.value)
    detail.value = r.data
  } catch { detail.value = null } finally { loading.value = false }
}

/** 只取模型类参数：依赖后端 isModelField 标记，兼容旧数据回退到正则 */
function isModelParam(p: RHWorkflowParam) {
  return !!p.modelMeta || p.isModelField === true || /name|path|ckpt|lora/i.test(p.fieldName)
}

const workflowOptions = computed(() =>
  workflows.value.map(w => ({ label: w.name || w.workflowId, value: w.workflowId }))
)

/** modelGroups + 对应 params */
const modelGroupsWithParams = computed(() => {
  if (!detail.value) return []
  const params = detail.value.analyzedParams ?? []
  const groups = detail.value.modelGroups ?? []
  if (!groups.length) {
    const modelParams = params.filter(isModelParam)
    if (!modelParams.length) return []
    return [{ groupName: '全局模型', samplerNodeId: '', modelNodeIds: [], params: modelParams }]
  }
  return groups.map(g => ({
    ...g,
    params: params.filter(p => g.modelNodeIds.includes(p.nodeId) && isModelParam(p)),
  })).filter(g => g.params.length)
})

/** 把 overrides 叠加到 params 上供报告使用 */
const effectiveParams = computed(() => {
  if (!detail.value) return []
  return detail.value.analyzedParams.filter(isModelParam).map(p => {
    const key = `${p.nodeId}::${p.fieldName}`
    const ov = overrides.value.get(key)
    if (!ov) return p
    return { ...p, currentValue: ov.value, modelMeta: ov.meta ? { ...p.modelMeta, ...ov.meta } : p.modelMeta }
  })
})

/** 兼容性报告 — 与工作流编辑器共用 useModelCompat 投票算法 */
interface CompatItem { label: string; value: string; baseModel: string; ok: 'ok' | 'warn' | 'err' }
const { compatStatus } = useModelCompat(effectiveParams)
const compatReport = computed((): CompatItem[] =>
  effectiveParams.value.map(p => ({
    label: p.label,
    value: String(p.currentValue),
    baseModel: p.modelMeta?.baseModel ?? '',
    ok: compatStatus(p),
  })),
)

const allOk = computed(() => compatReport.value.every(i => i.ok === 'ok'))
const hasChanges = computed(() => overrides.value.size > 0)

function handleReplace(nodeId: string, fieldName: string, value: string, meta?: ModelSearchResult) {
  overrides.value.set(`${nodeId}::${fieldName}`, { value, meta })
}

async function handleSave() {
  if (!selectedId.value || !hasChanges.value) return
  saving.value = true
  try {
    const list = [...overrides.value.entries()].map(([k, v]) => {
      const [nodeId, fieldName] = k.split('::')
      return { nodeId, fieldName, value: v.value }
    })
    const r = await applyModelOverrides(selectedId.value, list)
    if (r.ok) {
      Message.success(r.message)
      await loadDetail()
    }
  } catch { Message.error('保存失败') } finally { saving.value = false }
}

onMounted(loadWorkflows)
</script>

<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- 顶部工作流选择 -->
    <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-700 shrink-0 bg-gray-900/60">
      <span class="text-xs text-gray-400 shrink-0">选择工作流</span>
      <a-select
        v-model="selectedId"
        :options="workflowOptions"
        size="small"
        class="w-72"
        placeholder="请选择工作流"
        @change="loadDetail"
      />
      <span v-if="detail" class="text-xs text-gray-500">
        {{ detail.analyzedParams?.filter(isModelParam).length ?? 0 }} 个模型槽
      </span>
    </div>

    <!-- 主体：左右分栏 -->
    <div v-if="detail && !loading" class="flex-1 flex overflow-hidden">
      <!-- 左：模型组 -->
      <div class="w-1/2 overflow-y-auto p-4 space-y-3 border-r border-gray-700">
        <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">模型槽位</h3>
        <div v-if="!modelGroupsWithParams.length" class="text-xs text-gray-500 py-8 text-center">
          <Icon icon="lucide:alert-circle" class="w-6 h-6 mx-auto mb-2 opacity-40" />
          该工作流无可识别的模型参数（缓存可能未初始化）
        </div>
        <ModelGroupItem
          v-for="g in modelGroupsWithParams"
          :key="g.samplerNodeId || g.groupName"
          :group-name="g.groupName"
          :params="g.params"
          @replace="handleReplace"
        />
      </div>

      <!-- 右：兼容性报告 -->
      <div class="w-1/2 overflow-y-auto p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wider">兼容性报告</h3>
          <span
            class="text-xs px-2 py-0.5 rounded-full"
            :class="allOk ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'"
          >
            {{ allOk ? '全部兼容' : '存在冲突' }}
          </span>
        </div>

        <div v-if="!compatReport.length" class="text-xs text-gray-500 text-center py-8">暂无数据</div>

        <div class="space-y-2">
          <div
            v-for="item in compatReport"
            :key="item.label + item.value"
            class="flex items-start gap-2 px-3 py-2 rounded-lg border"
            :class="{
              'border-green-700/40 bg-green-900/10': item.ok === 'ok',
              'border-yellow-700/40 bg-yellow-900/10': item.ok === 'warn',
              'border-red-700/40 bg-red-900/10': item.ok === 'err',
            }"
          >
            <Icon
              :icon="item.ok === 'ok' ? 'lucide:check-circle' : item.ok === 'warn' ? 'lucide:help-circle' : 'lucide:x-circle'"
              class="w-3.5 h-3.5 mt-0.5 shrink-0"
              :class="{ 'text-green-400': item.ok === 'ok', 'text-yellow-400': item.ok === 'warn', 'text-red-400': item.ok === 'err' }"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-medium text-gray-200">{{ item.label }}</span>
                <span v-if="item.baseModel" class="text-[10px] text-gray-500 font-mono bg-gray-800 px-1 rounded">
                  {{ item.baseModel }}
                </span>
              </div>
              <div class="text-[10px] text-gray-500 truncate mt-0.5">{{ item.value }}</div>
              <div v-if="item.ok === 'err'" class="text-[10px] text-red-400 mt-0.5">架构与主模型不一致</div>
              <div v-else-if="item.ok === 'warn'" class="text-[10px] text-yellow-400 mt-0.5">无缓存元数据，无法判断兼容性</div>
            </div>
          </div>
        </div>

        <!-- 保存按钮 -->
        <div v-if="hasChanges" class="mt-4 pt-3 border-t border-gray-700">
          <a-button
            type="primary"
            size="small"
            :loading="saving"
            class="w-full"
            @click="handleSave"
          >
            <template #icon><Icon icon="lucide:save" class="w-3 h-3" /></template>
            应用 {{ overrides.size }} 条替换并保存
          </a-button>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="flex-1 flex items-center justify-center">
      <Icon icon="lucide:loader-2" class="w-8 h-8 text-blue-400 animate-spin" />
    </div>

    <!-- 空状态 -->
    <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-500 gap-3">
      <Icon icon="lucide:git-branch" class="w-12 h-12 opacity-30" />
      <span class="text-sm">选择一个工作流开始检测</span>
    </div>
  </div>
</template>
