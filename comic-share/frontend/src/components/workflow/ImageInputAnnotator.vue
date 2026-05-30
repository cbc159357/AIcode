<script setup lang="ts">
import { ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { Message } from '@arco-design/web-vue'
import { updateImageInputs, type ImageInput, type ImageInputRole } from '@/services/runninghub'

const props = defineProps<{
  workflowId: string
  imageInputs: ImageInput[]
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved', inputs: ImageInput[]): void
}>()

const saving = ref(false)
const localInputs = ref<ImageInput[]>([])

watch(() => props.visible, (v) => {
  if (v) localInputs.value = props.imageInputs.map(i => ({ ...i }))
})

const ROLE_OPTIONS: { value: ImageInputRole; label: string; color: string }[] = [
  { value: 'reference', label: '参考图', color: 'blue' },
  { value: 'face',      label: '脸部参考', color: 'purple' },
  { value: 'style',     label: '风格参考', color: 'cyan' },
  { value: 'pose',      label: '骨骼/姿势', color: 'orange' },
  { value: 'mask',      label: '遮罩', color: 'yellow' },
  { value: 'background', label: '背景', color: 'green' },
  { value: 'internal',  label: '内部节点', color: 'gray' },
]

const roleBadgeClass: Record<ImageInputRole, string> = {
  reference:  'bg-blue-600/20 text-blue-300 border-blue-600/40',
  face:       'bg-purple-600/20 text-purple-300 border-purple-600/40',
  style:      'bg-cyan-600/20 text-cyan-300 border-cyan-600/40',
  pose:       'bg-orange-600/20 text-orange-300 border-orange-600/40',
  mask:       'bg-yellow-600/20 text-yellow-300 border-yellow-600/40',
  background: 'bg-green-600/20 text-green-300 border-green-600/40',
  internal:   'bg-gray-600/20 text-gray-400 border-gray-600/40',
}

function updateRole(idx: number, role: ImageInputRole) {
  localInputs.value[idx].role = role
  localInputs.value[idx].required = role === 'reference'
}

async function handleSave() {
  saving.value = true
  try {
    await updateImageInputs(props.workflowId, localInputs.value)
    Message.success('标注已保存')
    emit('saved', localInputs.value)
    emit('update:visible', false)
  } catch (e) {
    Message.error(`保存失败: ${e}`)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <a-modal
    :visible="visible"
    title="图片输入语义标注"
    width="660px"
    :footer="false"
    @cancel="$emit('update:visible', false)"
  >
    <div class="space-y-1 mb-4 text-xs text-gray-400">
      <p>系统已通过下游连接启发式推断每个 <code class="text-blue-300">LoadImage</code> 节点的语义角色，请确认或修正。</p>
      <p>标记为「内部节点」的输入将在参数编辑器中隐藏。</p>
    </div>

    <div class="space-y-3 max-h-96 overflow-y-auto pr-1">
      <div
        v-for="(inp, idx) in localInputs"
        :key="inp.nodeId"
        class="rounded-lg border border-gray-700/60 bg-gray-800/40 p-3"
      >
        <!-- 节点信息行 -->
        <div class="flex items-center gap-2 mb-2">
          <Icon icon="lucide:image" class="w-4 h-4 text-gray-500 shrink-0" />
          <span class="text-xs text-gray-300 font-mono">节点 {{ inp.nodeId }}</span>
          <span
            class="text-xs px-1.5 py-0.5 rounded border"
            :class="roleBadgeClass[inp.role]"
          >
            {{ ROLE_OPTIONS.find(r => r.value === inp.role)?.label }}
          </span>
          <span v-if="inp.required" class="text-xs text-red-400">必填</span>
        </div>

        <!-- 标签编辑 -->
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs text-gray-500 w-10 shrink-0">标签</span>
          <a-input
            v-model="localInputs[idx].label"
            size="mini"
            class="flex-1"
            placeholder="显示给用户的名称"
          />
        </div>

        <!-- 角色选择 -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500 w-10 shrink-0">角色</span>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="opt in ROLE_OPTIONS"
              :key="opt.value"
              class="text-xs px-2 py-0.5 rounded border transition-colors"
              :class="inp.role === opt.value
                ? roleBadgeClass[opt.value]
                : 'border-gray-700 text-gray-500 hover:border-gray-500'"
              @click="updateRole(idx, opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="!localInputs.length" class="text-center py-8 text-xs text-gray-500">
        该工作流无 LoadImage 节点
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="flex items-center justify-between mt-4 pt-3 border-t border-gray-700/50">
      <span class="text-xs text-gray-500">共 {{ localInputs.length }} 个图片输入节点</span>
      <div class="flex gap-2">
        <a-button size="small" @click="$emit('update:visible', false)">取消</a-button>
        <a-button type="primary" size="small" :loading="saving" @click="handleSave">
          <template #icon><Icon icon="lucide:save" class="w-3 h-3" /></template>
          保存标注
        </a-button>
      </div>
    </div>
  </a-modal>
</template>
