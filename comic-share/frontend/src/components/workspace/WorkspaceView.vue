<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { useProjectStore } from '@/stores/project'
import { usePipeline } from '@/composables/usePipeline'
import { listArchives, createArchive } from '@/services/archives'
import type { Archive } from '@/types'
import ShotGrid from '@/components/shots/ShotGrid.vue'
import LLMOutput from '@/components/preview/LLMOutput.vue'

const projectStore = useProjectStore()
const { stepStatuses, llmOutput, isStreaming, runStep } = usePipeline()

const storyText = ref('')
const activeTab = ref<'shots' | 'llm'>('shots')

const archives = ref<Archive[]>([])
const selectedArchiveId = ref('')
const newName = ref('')
const showCreate = ref(false)

async function fetchArchives() {
  try {
    archives.value = await listArchives()
    if (archives.value.length && !selectedArchiveId.value) {
      selectedArchiveId.value = archives.value[0].id
    }
  } catch {
    archives.value = []
  }
}

async function handleCreate() {
  const name = newName.value.trim()
  if (!name) return
  const created = await createArchive(name)
  archives.value.unshift(created)
  selectedArchiveId.value = created.id
  newName.value = ''
  showCreate.value = false
}

onMounted(fetchArchives)

async function handleRunStep(step: number) {
  await runStep(step, storyText.value)
}
</script>

<template>
  <div class="flex h-full overflow-hidden">
    <!-- 左侧面板：归档选择 + 故事输入 + 流程控制 -->
    <aside class="w-80 bg-gray-800/80 border-r border-gray-700 overflow-y-auto p-4 flex flex-col gap-4 shrink-0">
      <!-- 归档选择 -->
      <div class="flex items-center gap-2">
        <Icon icon="lucide:folder-archive" class="w-4 h-4 text-blue-400 shrink-0" />
        <a-select
          v-model="selectedArchiveId"
          :options="archives.map(a => ({ label: a.name, value: a.id }))"
          size="small"
          class="flex-1"
          placeholder="选择归档"
          allow-clear
        />
        <a-button size="mini" @click="showCreate = !showCreate">
          <template #icon><Icon icon="lucide:plus" class="w-3 h-3" /></template>
        </a-button>
      </div>
      <div v-if="showCreate" class="flex items-center gap-2 -mt-2">
        <a-input v-model="newName" size="small" placeholder="归档名称" @press-enter="handleCreate" />
        <a-button size="mini" type="primary" @click="handleCreate">创建</a-button>
      </div>

      <!-- 故事输入 -->
      <div class="rounded-lg bg-gray-900/50 p-4">
        <h3 class="text-sm font-bold text-gray-300 mb-2">故事输入</h3>
        <a-textarea
          v-model="storyText"
          :auto-size="{ minRows: 5, maxRows: 10 }"
          placeholder="输入你的故事文本..."
        />
      </div>

      <!-- 流程控制 -->
      <div class="rounded-lg bg-gray-900/50 p-4">
        <h3 class="text-sm font-bold text-gray-300 mb-3">流程控制</h3>
        <div class="flex flex-col gap-2">
          <a-button
            v-for="step in 4"
            :key="step"
            :disabled="stepStatuses[step] === 'running' || (step > 1 && stepStatuses[step - 1] !== 'done')"
            :loading="stepStatuses[step] === 'running'"
            :type="stepStatuses[step] === 'done' ? 'outline' : 'primary'"
            :status="stepStatuses[step] === 'done' ? 'success' : stepStatuses[step] === 'error' ? 'danger' : undefined"
            long
            @click="handleRunStep(step)"
          >
            {{ stepStatuses[step] === 'done' ? '✓ ' : '' }}步骤{{ step }}:
            {{ step === 1 ? '生成剧本' : step === 2 ? '生成图片' : step === 3 ? '语音合成' : '视频合成' }}
          </a-button>
        </div>
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- Tab 切换 -->
      <div class="flex border-b border-gray-700 px-4 shrink-0">
        <button
          class="px-4 py-2 text-sm transition"
          :class="activeTab === 'shots' ? 'text-white border-b-2 border-blue-500' : 'text-gray-400 hover:text-white'"
          @click="activeTab = 'shots'"
        >
          分镜板
        </button>
        <button
          class="px-4 py-2 text-sm transition"
          :class="activeTab === 'llm' ? 'text-white border-b-2 border-blue-500' : 'text-gray-400 hover:text-white'"
          @click="activeTab = 'llm'"
        >
          LLM 输出
        </button>
      </div>

      <!-- Tab 内容 -->
      <div class="flex-1 overflow-hidden">
        <ShotGrid v-show="activeTab === 'shots'" :shots="projectStore.shots" />
        <LLMOutput v-show="activeTab === 'llm'" :text="llmOutput" :streaming="isStreaming" />
      </div>
    </main>
  </div>
</template>
