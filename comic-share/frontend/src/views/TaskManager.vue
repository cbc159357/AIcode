<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import {
  listArchives,
  createArchive,
  renameArchive,
  deleteArchive,
  listTasks,
  deleteTask,
  listMedia,
} from '@/services/archives'
import type { Archive, Task, MediaItem } from '@/types'
import MediaGallery from '@/components/tasks/MediaGallery.vue'

const archives = ref<Archive[]>([])
const tasks = ref<Task[]>([])
const media = ref<MediaItem[]>([])

const selectedArchiveId = ref('')
const selectedTaskId = ref('')
const newArchiveName = ref('')
const showCreate = ref(false)
const renaming = ref(false)
const renameValue = ref('')
const loading = ref(false)

type MediaFilterType = 'all' | 'image' | 'audio' | 'video'
const mediaFilter = ref<MediaFilterType>('all')
const filterOptions = [
  { value: 'all', label: '全部' },
  { value: 'image', label: '图片' },
  { value: 'audio', label: '音频' },
  { value: 'video', label: '视频' },
]

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

async function fetchTasks() {
  if (!selectedArchiveId.value) {
    tasks.value = []
    return
  }
  tasks.value = await listTasks(selectedArchiveId.value)
  if (tasks.value.length) {
    selectedTaskId.value = tasks.value[0].id
  } else {
    selectedTaskId.value = ''
  }
}

async function fetchMedia() {
  if (!selectedArchiveId.value || !selectedTaskId.value) {
    media.value = []
    return
  }
  loading.value = true
  try {
    media.value = await listMedia(selectedArchiveId.value, selectedTaskId.value)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  const name = newArchiveName.value.trim()
  if (!name) return
  const created = await createArchive(name)
  archives.value.unshift(created)
  selectedArchiveId.value = created.id
  newArchiveName.value = ''
  showCreate.value = false
}

async function handleRename() {
  const name = renameValue.value.trim()
  if (!name || !selectedArchiveId.value) return
  await renameArchive(selectedArchiveId.value, name)
  const arc = archives.value.find(a => a.id === selectedArchiveId.value)
  if (arc) arc.name = name
  renaming.value = false
}

async function handleDeleteArchive() {
  if (!selectedArchiveId.value) return
  await deleteArchive(selectedArchiveId.value)
  archives.value = archives.value.filter(a => a.id !== selectedArchiveId.value)
  selectedArchiveId.value = archives.value[0]?.id ?? ''
}

async function handleDeleteTask(taskId: string) {
  if (!selectedArchiveId.value) return
  await deleteTask(selectedArchiveId.value, taskId)
  tasks.value = tasks.value.filter(t => t.id !== taskId)
  if (selectedTaskId.value === taskId) {
    selectedTaskId.value = tasks.value[0]?.id ?? ''
  }
}

function formatTaskLabel(id: string): string {
  return id.replace('task_', '').replace(/_/g, ' ')
}

function startRename() {
  const arc = archives.value.find(a => a.id === selectedArchiveId.value)
  renameValue.value = arc?.name ?? ''
  renaming.value = true
}

watch(selectedArchiveId, () => {
  selectedTaskId.value = ''
  media.value = []
  fetchTasks()
})

watch(selectedTaskId, fetchMedia)

onMounted(fetchArchives)
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- 顶栏：归档选择 + 操作 -->
    <header class="flex items-center gap-3 px-5 py-3 border-b border-gray-700 bg-gray-800/60 shrink-0">
      <Icon icon="lucide:folder-archive" class="w-5 h-5 text-blue-400" />
      <h2 class="text-sm font-bold text-white">任务管理</h2>

      <div class="w-px h-5 bg-gray-700 mx-1" />

      <!-- 归档下拉 -->
      <a-select
        v-model="selectedArchiveId"
        :options="archives.map(a => ({ label: a.name, value: a.id }))"
        size="small"
        class="w-44"
        placeholder="选择归档"
      />

      <!-- 操作按钮组 -->
      <a-button-group size="mini">
        <a-button @click="showCreate = !showCreate" title="新建归档">
          <template #icon><Icon icon="lucide:plus" class="w-3 h-3" /></template>
        </a-button>
        <a-button :disabled="!selectedArchiveId" @click="startRename" title="重命名">
          <template #icon><Icon icon="lucide:pencil" class="w-3 h-3" /></template>
        </a-button>
        <a-popconfirm content="确定删除此归档及其全部任务？" @ok="handleDeleteArchive">
          <a-button :disabled="!selectedArchiveId" status="danger" title="删除归档">
            <template #icon><Icon icon="lucide:trash-2" class="w-3 h-3" /></template>
          </a-button>
        </a-popconfirm>
      </a-button-group>

      <div class="flex-1" />

      <!-- 媒体类型筛选 -->
      <a-select
        v-model="mediaFilter"
        :options="filterOptions"
        size="small"
        class="w-28"
      />

      <!-- 新建/重命名输入 -->
      <template v-if="showCreate">
        <a-input
          v-model="newArchiveName"
          size="small"
          class="w-36"
          placeholder="归档名称"
          @press-enter="handleCreate"
        />
        <a-button size="mini" type="primary" @click="handleCreate">创建</a-button>
      </template>
      <template v-if="renaming">
        <a-input
          v-model="renameValue"
          size="small"
          class="w-36"
          placeholder="新名称"
          @press-enter="handleRename"
        />
        <a-button size="mini" type="primary" @click="handleRename">确定</a-button>
        <a-button size="mini" @click="renaming = false">取消</a-button>
      </template>
    </header>

    <!-- 主体：左侧子任务树 + 右侧媒体画廊 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 左侧：子任务列表 -->
      <aside class="w-56 bg-gray-800/40 border-r border-gray-700/50 flex flex-col shrink-0 overflow-hidden">
        <div class="px-3 py-2 text-xs text-gray-400 border-b border-gray-700/30 shrink-0">
          子任务 ({{ tasks.length }})
        </div>
        <div class="flex-1 overflow-y-auto">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="group flex items-center gap-2 px-3 py-2.5 cursor-pointer border-b border-gray-700/20 transition-colors"
            :class="selectedTaskId === task.id
              ? 'bg-blue-600/10 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/20'"
            @click="selectedTaskId = task.id"
          >
            <!-- 状态指示器 -->
            <span
              class="w-2 h-2 rounded-full shrink-0"
              :class="{
                'bg-green-400': task.status === 'completed',
                'bg-yellow-400 animate-pulse': task.status === 'running',
                'bg-red-400': task.status === 'failed',
              }"
            />

            <!-- 任务信息 -->
            <div class="flex-1 min-w-0">
              <div class="text-xs font-medium truncate">{{ formatTaskLabel(task.id) }}</div>
              <div class="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                <span v-if="task.media_count.image">
                  <Icon icon="lucide:image" class="w-3 h-3 inline" /> {{ task.media_count.image }}
                </span>
                <span v-if="task.media_count.audio">
                  <Icon icon="lucide:music" class="w-3 h-3 inline" /> {{ task.media_count.audio }}
                </span>
                <span v-if="task.media_count.video">
                  <Icon icon="lucide:film" class="w-3 h-3 inline" /> {{ task.media_count.video }}
                </span>
              </div>
            </div>

            <!-- 删除按钮 -->
            <a-popconfirm content="删除此任务？" @ok="handleDeleteTask(task.id)">
              <button
                class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-600/20 text-gray-500 hover:text-red-400 transition"
                @click.stop
              >
                <Icon icon="lucide:x" class="w-3 h-3" />
              </button>
            </a-popconfirm>
          </div>

          <!-- 空状态 -->
          <div v-if="!tasks.length && selectedArchiveId" class="flex flex-col items-center justify-center h-32 text-gray-500">
            <Icon icon="lucide:inbox" class="w-6 h-6 mb-1 opacity-40" />
            <span class="text-xs">暂无任务</span>
          </div>
          <div v-if="!selectedArchiveId" class="flex flex-col items-center justify-center h-32 text-gray-500">
            <Icon icon="lucide:folder-open" class="w-6 h-6 mb-1 opacity-40" />
            <span class="text-xs">请先选择或创建归档</span>
          </div>
        </div>
      </aside>

      <!-- 右侧：媒体画廊 -->
      <div class="flex-1 overflow-hidden">
        <MediaGallery :media="media" :loading="loading" :filter="mediaFilter" />
      </div>
    </div>
  </div>
</template>
