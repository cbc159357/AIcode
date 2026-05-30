<script setup lang="ts">
import { ref, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { Message } from '@arco-design/web-vue'
import {
  getSavedWorkflow,
  saveWorkflow,
  fetchWorkflowJson,
  deleteWorkflow,
  uploadImageToRH,
  type RHWorkflowItem,
  type RHWorkflowParam,
  type ImageInput,
  type ImageInputRole,
  type ParamGroup,
} from '@/services/runninghub'
import ParamEditor from './ParamEditor.vue'
import TaskRunner from './TaskRunner.vue'
import ImageInputAnnotator from './ImageInputAnnotator.vue'

const props = defineProps<{
  workflow: RHWorkflowItem
}>()

const emit = defineEmits<{
  (e: 'deleted', workflowId: string): void
}>()

const expanded = ref(false)
const loading = ref(false)
const params = ref<RHWorkflowParam[]>([])
const originalParams = ref<RHWorkflowParam[]>([])
const imageInputs = ref<ImageInput[]>([])
const paramGroups = ref<ParamGroup[]>([])
const refreshing = ref(false)
const showAnnotator = ref(false)

const visibleImageInputs = computed(() =>
  imageInputs.value.filter(i => i.role !== 'internal')
)

const excludeNodeIds = computed(() =>
  imageInputs.value.map(i => i.nodeId)
)

const roleBadgeClass: Record<ImageInputRole, string> = {
  reference:  'bg-blue-600/20 text-blue-300 border-blue-600/40',
  face:       'bg-purple-600/20 text-purple-300 border-purple-600/40',
  style:      'bg-cyan-600/20 text-cyan-300 border-cyan-600/40',
  pose:       'bg-orange-600/20 text-orange-300 border-orange-600/40',
  mask:       'bg-yellow-600/20 text-yellow-300 border-yellow-600/40',
  background: 'bg-green-600/20 text-green-300 border-green-600/40',
  internal:   'bg-gray-600/20 text-gray-400 border-gray-600/40',
}

const roleLabel: Record<ImageInputRole, string> = {
  reference: '参考图', face: '脸部', style: '风格',
  pose: '骨骼', mask: '遮罩', background: '背景', internal: '内部',
}

async function toggleExpand() {
  expanded.value = !expanded.value
  if (expanded.value && !params.value.length) {
    loading.value = true
    try {
      const { data } = await getSavedWorkflow(props.workflow.workflowId)
      params.value = structuredClone(data.analyzedParams || [])
      originalParams.value = structuredClone(data.analyzedParams || [])
      imageInputs.value = structuredClone(data.imageInputs || [])
      paramGroups.value = structuredClone(data.paramGroups || [])
    } finally {
      loading.value = false
    }
  }
}

function handleParamUpdate(index: number, value: string | number | boolean) {
  params.value[index].currentValue = value
}

async function handleRefresh() {
  refreshing.value = true
  try {
    const fetchResp = await fetchWorkflowJson(props.workflow.workflowId)
    if (!fetchResp.ok) { Message.error(fetchResp.message); return }
    await saveWorkflow({
      workflow_id: props.workflow.workflowId,
      name: props.workflow.name,
      description: props.workflow.description,
      group: props.workflow.group,
      raw_nodes: fetchResp.data ?? undefined,
    })
    const { data } = await getSavedWorkflow(props.workflow.workflowId)
    params.value = structuredClone(data.analyzedParams || [])
    originalParams.value = structuredClone(data.analyzedParams || [])
    imageInputs.value = structuredClone(data.imageInputs || [])
    paramGroups.value = structuredClone(data.paramGroups || [])
    Message.success('已重新拉取并更新')
  } catch {
    Message.error('刷新失败，请检查 API Key 和网络')
  } finally {
    refreshing.value = false
  }
}

async function handleDelete() {
  await deleteWorkflow(props.workflow.workflowId)
  emit('deleted', props.workflow.workflowId)
}

async function handleImageUpload(idx: number, event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const result = await uploadImageToRH(file)
  if (result.ok) {
    imageInputs.value[idx].uploadedFileName = result.fileName
    Message.success(`已上传: ${result.fileName}`)
  } else {
    Message.error(`上传失败: ${result.message}`)
  }
}

function onAnnotatorSaved(updated: ImageInput[]) {
  imageInputs.value = updated
}

const imageNodeInfoList = computed(() =>
  visibleImageInputs.value
    .filter(i => i.uploadedFileName)
    .map(i => ({ nodeId: i.nodeId, fieldName: i.fieldName, fieldValue: i.uploadedFileName! }))
)
</script>

<template>
  <div class="rounded-lg bg-gray-800/60 border border-gray-700 overflow-hidden">
    <!-- 卡片头 -->
    <div
      class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-700/20 transition"
      @click="toggleExpand"
    >
      <Icon
        :icon="expanded ? 'lucide:chevron-down' : 'lucide:chevron-right'"
        class="w-4 h-4 text-gray-400 shrink-0"
      />
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <span class="text-sm text-white font-medium truncate">{{ workflow.name }}</span>
          <span class="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">{{ workflow.workflowId }}</span>
        </div>
        <div class="text-xs text-gray-500 mt-0.5 truncate">{{ workflow.description }}</div>
      </div>

      <div class="flex items-center gap-2 shrink-0 text-xs text-gray-500">
        <span v-if="workflow.group" class="px-1.5 py-0.5 rounded bg-blue-600/10 text-blue-400">{{ workflow.group }}</span>
        <span>{{ workflow.nodeCount }} 节点</span>
        <span v-if="workflow.imageInputCount" class="px-1.5 py-0.5 rounded bg-gray-700/60 text-gray-400">
          {{ workflow.imageInputCount }} 图片输入
        </span>
        <span
          v-if="workflow.imageInputCount && !workflow.imageInputsAnnotated"
          class="px-1.5 py-0.5 rounded bg-yellow-600/20 text-yellow-400 text-xs"
        >待标注</span>
      </div>

      <a-button size="mini" :loading="refreshing" @click.stop="handleRefresh">
        <template #icon><Icon icon="lucide:refresh-cw" class="w-3 h-3" /></template>
      </a-button>

      <a-popconfirm content="确定删除此工作流？" @ok="handleDelete">
        <a-button size="mini" status="danger" @click.stop>
          <template #icon><Icon icon="lucide:trash-2" class="w-3 h-3" /></template>
        </a-button>
      </a-popconfirm>
    </div>

    <!-- 展开区域 -->
    <div v-if="expanded" class="border-t border-gray-700/50 px-4 py-3">
      <a-spin :loading="loading" class="w-full">
        <div class="space-y-4">

          <!-- 图片输入区 -->
          <div v-if="imageInputs.length">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-xs font-bold text-gray-400">图片输入</h3>
              <a-button size="mini" @click.stop="showAnnotator = true">
                <template #icon><Icon icon="lucide:tag" class="w-3 h-3" /></template>
                标注语义
              </a-button>
            </div>

            <div class="space-y-2">
              <div
                v-for="(inp, idx) in visibleImageInputs"
                :key="inp.nodeId"
                class="flex items-center gap-2 rounded border border-gray-700/50 bg-gray-900/30 px-3 py-2"
              >
                <!-- 角色徽章 + 标签 -->
                <span
                  class="text-xs px-1.5 py-0.5 rounded border shrink-0"
                  :class="roleBadgeClass[inp.role]"
                >{{ roleLabel[inp.role] }}</span>
                <span class="text-xs text-gray-300 flex-1 truncate">{{ inp.label }}</span>
                <span v-if="inp.required" class="text-xs text-red-400 shrink-0">必填</span>

                <!-- 上传状态 / 按钮 -->
                <span
                  v-if="inp.uploadedFileName"
                  class="text-xs text-green-400 truncate max-w-32 shrink-0"
                  :title="inp.uploadedFileName"
                >
                  <Icon icon="lucide:check" class="inline w-3 h-3 mr-0.5" />{{ inp.uploadedFileName }}
                </span>
                <label class="cursor-pointer shrink-0">
                  <input
                    type="file"
                    accept="image/*"
                    class="hidden"
                    @change="handleImageUpload(idx, $event)"
                  />
                  <a-button size="mini" tag="span">
                    <template #icon><Icon icon="lucide:upload" class="w-3 h-3" /></template>
                    {{ inp.uploadedFileName ? '换图' : '上传' }}
                  </a-button>
                </label>
              </div>
            </div>
          </div>

          <!-- 常规参数编辑器 -->
          <div>
            <h3 class="text-xs font-bold text-gray-400 mb-2">可调参数</h3>
            <ParamEditor
              :params="params"
              :param-groups="paramGroups.length ? paramGroups : undefined"
              :exclude-node-ids="excludeNodeIds"
              @update="handleParamUpdate"
            />
          </div>

          <!-- 任务执行 -->
          <TaskRunner
            :workflow-id="workflow.workflowId"
            :params="params"
            :original-params="originalParams"
            :extra-node-info="imageNodeInfoList"
          />
        </div>
      </a-spin>
    </div>

    <!-- 标注弹窗 -->
    <ImageInputAnnotator
      v-model:visible="showAnnotator"
      :workflow-id="workflow.workflowId"
      :image-inputs="imageInputs"
      @saved="onAnnotatorSaved"
    />
  </div>
</template>
