<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import {
  listArchives,
  createArchive,
  listTasks,
  listMedia,
} from '@/services/archives'
import type { Archive, Task, MediaItem } from '@/types'
import MediaGallery from './MediaGallery.vue'

const archives = ref<Archive[]>([])
const tasks = ref<Task[]>([])
const media = ref<MediaItem[]>([])
const selectedArchiveId = ref('')
const selectedTaskId = ref('')
const newArchiveName = ref('')
const showCreate = ref(false)
const expanded = ref(false)
const loading = ref(false)
const mediaFilter = ref<'all' | 'image' | 'audio' | 'video'>('all')

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
  if (tasks.value.length && !selectedTaskId.value) {
    selectedTaskId.value = tasks.value[0].id
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
  if (!newArchiveName.value.trim()) return
  const created = await createArchive(newArchiveName.value.trim())
  archives.value.unshift(created)
  selectedArchiveId.value = created.id
  newArchiveName.value = ''
  showCreate.value = false
}

watch(selectedArchiveId, () => {
  selectedTaskId.value = ''
  media.value = []
  fetchTasks()
})

watch(selectedTaskId, () => {
  fetchMedia()
})

onMounted(fetchArchives)
</script>

<template>
  <div class="border-b border-gray-700 bg-gray-800/60">
    <!-- 归档选择栏 -->
    <div class="flex items-center gap-3 px-4 py-2">
      <Icon icon="lucide:folder-archive" class="w-4 h-4 text-blue-400 shrink-0" />

      <a-select
        v-model="selectedArchiveId"
        :options="archives.map(a => ({ label: a.name, value: a.id }))"
        size="small"
        class="w-40"
        placeholder="选择归档"
        allow-clear
      />

      <a-button size="mini" @click="showCreate = !showCreate">
        <template #icon><Icon icon="lucide:plus" class="w-3 h-3" /></template>
      </a-button>

      <!-- 新建归档输入 -->
      <template v-if="showCreate">
        <a-input
          v-model="newArchiveName"
          size="small"
          class="w-32"
          placeholder="归档名称"
          @press-enter="handleCreate"
        />
        <a-button size="mini" type="primary" @click="handleCreate">创建</a-button>
      </template>

      <div class="flex-1" />

      <!-- 展开/折叠任务列表 -->
      <a-button
        v-if="selectedArchiveId"
        size="mini"
        @click="expanded = !expanded"
      >
        <template #icon>
          <Icon :icon="expanded ? 'lucide:chevron-up' : 'lucide:chevron-down'" class="w-3 h-3" />
        </template>
        {{ tasks.length }} 个任务
      </a-button>
    </div>

    <!-- 展开区域：任务列表 + 媒体画廊 -->
    <div v-if="expanded && selectedArchiveId" class="border-t border-gray-700/50">
      <div class="flex h-64 overflow-hidden">
        <!-- 左侧：子任务列表 -->
        <aside class="w-48 border-r border-gray-700/50 overflow-y-auto shrink-0">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="px-3 py-2 text-xs cursor-pointer transition-colors"
            :class="selectedTaskId === task.id
              ? 'bg-blue-600/10 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/30'"
            @click="selectedTaskId = task.id"
          >
            <div class="font-medium truncate">{{ task.id.replace('task_', '') }}</div>
            <div class="flex items-center gap-1 mt-0.5">
              <span
                class="w-1.5 h-1.5 rounded-full"
                :class="{
                  'bg-green-400': task.status === 'completed',
                  'bg-yellow-400 animate-pulse': task.status === 'running',
                  'bg-red-400': task.status === 'failed',
                }"
              />
              <span class="text-gray-500">{{ task.status }}</span>
            </div>
          </div>
          <div v-if="!tasks.length" class="p-3 text-xs text-gray-500 text-center">
            暂无任务
          </div>
        </aside>

        <!-- 右侧：媒体画廊 -->
        <div class="flex-1 overflow-y-auto">
          <MediaGallery :media="media" :loading="loading" :filter="mediaFilter" />
        </div>
      </div>
    </div>
  </div>
</template>
