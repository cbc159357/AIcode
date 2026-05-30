<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import {
  createTask,
  pollTaskStatus,
  cancelTask,
  buildNodeInfoList,
  type RHWorkflowParam,
} from '@/services/runninghub'

const props = defineProps<{
  workflowId: string
  params: RHWorkflowParam[]
  originalParams: RHWorkflowParam[]
  /** 图片输入已上传的 nodeInfoList 条目（来自 WorkflowCard） */
  extraNodeInfo?: { nodeId: string; fieldName: string; fieldValue: string }[]
}>()

type TaskState = 'idle' | 'submitting' | 'queued' | 'running' | 'completed' | 'failed'

const taskState = ref<TaskState>('idle')
const taskId = ref('')
const taskMessage = ref('')
const outputs = ref<unknown[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

async function handleSubmit() {
  taskState.value = 'submitting'
  taskMessage.value = ''
  outputs.value = []
  try {
    const nodeInfoList = [
      ...(props.extraNodeInfo ?? []),
      ...buildNodeInfoList(props.params, props.originalParams),
    ]
    const result = await createTask(props.workflowId, nodeInfoList.length ? nodeInfoList : undefined)
    if (!result.ok) {
      taskState.value = 'failed'
      taskMessage.value = result.message
      return
    }
    taskId.value = result.taskId
    taskState.value = 'queued'
    startPolling()
  } catch (e) {
    taskState.value = 'failed'
    taskMessage.value = String(e)
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (!taskId.value) return
    try {
      const result = await pollTaskStatus(taskId.value)
      taskMessage.value = result.message
      if (result.status === 'COMPLETED') {
        taskState.value = 'completed'
        outputs.value = result.outputs
        stopPolling()
      } else if (result.status === 'FAILED') {
        taskState.value = 'failed'
        stopPolling()
      } else if (result.status === 'RUNNING') {
        taskState.value = 'running'
      }
    } catch {
      taskState.value = 'failed'
      taskMessage.value = '轮询异常'
      stopPolling()
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function handleCancel() {
  if (!taskId.value) return
  await cancelTask(taskId.value)
  stopPolling()
  taskState.value = 'idle'
  taskMessage.value = '已取消'
}

onUnmounted(stopPolling)

const stateIcon: Record<TaskState, string> = {
  idle: 'lucide:play',
  submitting: 'lucide:loader',
  queued: 'lucide:clock',
  running: 'lucide:loader',
  completed: 'lucide:check-circle',
  failed: 'lucide:x-circle',
}

const stateLabel: Record<TaskState, string> = {
  idle: '就绪',
  submitting: '提交中…',
  queued: '排队中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
}
</script>

<template>
  <div>
    <div class="flex items-center gap-3">
      <a-button
        type="primary"
        size="small"
        :loading="taskState === 'submitting'"
        :disabled="taskState === 'running' || taskState === 'queued'"
        @click="handleSubmit"
      >
        <template #icon><Icon icon="lucide:play" class="w-3 h-3" /></template>
        执行任务
      </a-button>

      <a-button
        v-if="taskState === 'queued' || taskState === 'running'"
        size="small"
        status="danger"
        @click="handleCancel"
      >
        取消
      </a-button>

      <!-- 状态显示 -->
      <div class="flex items-center gap-1.5 text-xs">
        <Icon
          :icon="stateIcon[taskState]"
          class="w-3.5 h-3.5"
          :class="{
            'text-gray-500': taskState === 'idle',
            'text-yellow-400 animate-spin': taskState === 'submitting' || taskState === 'running',
            'text-blue-400': taskState === 'queued',
            'text-green-400': taskState === 'completed',
            'text-red-400': taskState === 'failed',
          }"
        />
        <span class="text-gray-400">{{ stateLabel[taskState] }}</span>
        <span v-if="taskMessage" class="text-gray-500 truncate max-w-xs">— {{ taskMessage }}</span>
      </div>
    </div>

    <!-- 输出预览 -->
    <div v-if="outputs.length" class="mt-3 grid grid-cols-3 gap-2">
      <div
        v-for="(item, idx) in outputs"
        :key="idx"
        class="rounded bg-gray-900/60 border border-gray-700/50 overflow-hidden"
      >
        <img
          v-if="typeof item === 'object' && item !== null && 'fileUrl' in item"
          :src="(item as Record<string, string>).fileUrl"
          class="w-full aspect-square object-cover"
          loading="lazy"
        />
        <div v-else class="p-2 text-xs text-gray-400 truncate">
          {{ JSON.stringify(item) }}
        </div>
      </div>
    </div>
  </div>
</template>
