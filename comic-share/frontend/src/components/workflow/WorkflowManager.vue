<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { Message } from '@arco-design/web-vue'
import {
  listSavedWorkflows,
  fetchWorkflowJson,
  saveWorkflow,
  type RHWorkflowItem,
} from '@/services/runninghub'
import WorkflowCard from './WorkflowCard.vue'

const savedWorkflows = ref<RHWorkflowItem[]>([])
const loading = ref(false)

const addingId = ref('')
const addingName = ref('')
const addingLoading = ref(false)
const showAddForm = ref(false)

async function fetchSavedList() {
  loading.value = true
  try {
    const resp = await listSavedWorkflows()
    savedWorkflows.value = resp.items
  } catch {
    savedWorkflows.value = []
  } finally {
    loading.value = false
  }
}

function extractWorkflowId(input: string): string {
  const trimmed = input.trim()
  try {
    const url = new URL(trimmed)
    const segments = url.pathname.split('/').filter(Boolean)
    const idx = segments.indexOf('workflow')
    if (idx >= 0 && segments[idx + 1]) return segments[idx + 1]
  } catch {
    // 非 URL，直接使用
  }
  return trimmed
}

async function handleAdd() {
  if (!addingId.value.trim()) return
  addingId.value = extractWorkflowId(addingId.value)
  addingLoading.value = true
  try {
    const wfId = addingId.value
    const fetchResp = await fetchWorkflowJson(wfId)
    if (!fetchResp.ok) {
      Message.error(fetchResp.message)
      return
    }
    await saveWorkflow({
      workflow_id: wfId,
      name: addingName.value.trim() || wfId,
      raw_nodes: fetchResp.data ?? undefined,
    })
    Message.success('工作流已添加')
    addingId.value = ''
    addingName.value = ''
    showAddForm.value = false
    await fetchSavedList()
  } catch (e) {
    Message.error(`添加失败: ${e}`)
  } finally {
    addingLoading.value = false
  }
}

function handleDeleted(id: string) {
  savedWorkflows.value = savedWorkflows.value.filter(w => w.workflowId !== id)
}

onMounted(fetchSavedList)
</script>

<template>
  <div class="h-full overflow-y-auto p-6 space-y-6">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between">
      <h1 class="text-lg font-bold text-white">RunningHub 工作流</h1>
      <a-button size="small" @click="fetchSavedList">
        <template #icon><Icon icon="lucide:refresh-cw" class="w-4 h-4" /></template>
        刷新
      </a-button>
    </div>

    <!-- 添加工作流 -->
    <div class="rounded-lg bg-gray-800/60 border border-gray-700 p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-sm font-bold text-white">添加工作流</h2>
        <a-button size="mini" @click="showAddForm = !showAddForm">
          <template #icon><Icon :icon="showAddForm ? 'lucide:x' : 'lucide:plus'" class="w-3 h-3" /></template>
        </a-button>
      </div>
      <p class="text-xs text-gray-500 mb-3">输入 RunningHub 工作流 ID，自动拉取节点 JSON 并分析可调参数</p>

      <div v-if="showAddForm" class="flex items-center gap-2">
        <a-input v-model="addingId" size="small" class="w-64" placeholder="工作流 ID 或完整 URL" />
        <a-input v-model="addingName" size="small" class="w-36" placeholder="名称（可选）" />
        <a-button type="primary" size="small" :loading="addingLoading" @click="handleAdd">
          拉取 & 保存
        </a-button>
      </div>
    </div>

    <!-- 工作流列表 -->
    <div>
      <h2 class="text-sm font-bold text-gray-300 mb-3">
        已保存工作流 ({{ savedWorkflows.length }})
      </h2>

      <a-spin :loading="loading" class="w-full">
        <div v-if="savedWorkflows.length" class="space-y-2">
          <WorkflowCard
            v-for="wf in savedWorkflows"
            :key="wf.workflowId"
            :workflow="wf"
            @deleted="handleDeleted"
          />
        </div>

        <div v-else class="flex flex-col items-center justify-center py-16 text-gray-500">
          <Icon icon="lucide:folder-open" class="w-12 h-12 mb-3 opacity-40" />
          <span class="text-sm">暂无工作流</span>
          <span class="text-xs mt-1">点击上方「添加工作流」输入 RunningHub 工作流 ID</span>
        </div>
      </a-spin>
    </div>
  </div>
</template>
