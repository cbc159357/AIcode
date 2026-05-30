<script setup lang="ts">
import { ref, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { Message } from '@arco-design/web-vue'
import { uploadImageToRH, type ImageInput, type ImageInputRole } from '@/services/runninghub'
import ImageInputAnnotator from './ImageInputAnnotator.vue'

const props = defineProps<{
  workflowId: string
  imageInputs: ImageInput[]
}>()

const emit = defineEmits<{
  (e: 'uploaded', nodeId: string, fieldName: string, fileName: string): void
  (e: 'annotated', updated: ImageInput[]): void
}>()

const showAnnotator = ref(false)

const visibleImageInputs = computed(() =>
  props.imageInputs.filter(i => i.role !== 'internal'),
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

async function handleUpload(inp: ImageInput, event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const result = await uploadImageToRH(file)
  if (result.ok) {
    emit('uploaded', inp.nodeId, inp.fieldName, result.fileName)
    Message.success(`已上传: ${result.fileName}`)
  } else {
    Message.error(`上传失败: ${result.message}`)
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-xs font-bold text-gray-400">图片输入</h3>
      <a-button size="mini" @click.stop="showAnnotator = true">
        <template #icon><Icon icon="lucide:tag" class="w-3 h-3" /></template>
        标注语义
      </a-button>
    </div>
    <div class="space-y-2">
      <div
        v-for="inp in visibleImageInputs"
        :key="inp.nodeId"
        class="flex items-center gap-2 rounded border border-gray-700/50 bg-gray-900/30 px-3 py-2"
      >
        <span class="text-xs px-1.5 py-0.5 rounded border shrink-0" :class="roleBadgeClass[inp.role]">
          {{ roleLabel[inp.role] }}
        </span>
        <span class="text-xs text-gray-300 flex-1 truncate">{{ inp.label }}</span>
        <span v-if="inp.required" class="text-xs text-red-400 shrink-0">必填</span>
        <span
          v-if="inp.uploadedFileName"
          class="text-xs text-green-400 truncate max-w-32 shrink-0"
          :title="inp.uploadedFileName"
        >
          <Icon icon="lucide:check" class="inline w-3 h-3 mr-0.5" />{{ inp.uploadedFileName }}
        </span>
        <label class="cursor-pointer shrink-0">
          <input type="file" accept="image/*" class="hidden" @change="handleUpload(inp, $event)" />
          <a-button size="mini" tag="span">
            <template #icon><Icon icon="lucide:upload" class="w-3 h-3" /></template>
            {{ inp.uploadedFileName ? '换图' : '上传' }}
          </a-button>
        </label>
      </div>
    </div>
    <ImageInputAnnotator
      v-model:visible="showAnnotator"
      :workflow-id="workflowId"
      :image-inputs="imageInputs"
      @saved="emit('annotated', $event)"
    />
  </div>
</template>
