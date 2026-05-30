<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Icon } from '@iconify/vue'
import { saveRHConfig, getModelCacheStatus, refreshModelCache } from '@/services/runninghub'
import type { CacheProgress } from '@/services/runninghub'

const cacheExists = ref(false)
const cacheTotalCount = ref(0)
const cacheFetchedAt = ref<string | null>(null)
const cacheRefreshing = ref(false)
const cacheProgress = ref<CacheProgress | null>(null)
const cacheStrategy = ref('manual')

const strategyOptions = [
  { value: 'manual', label: '仅手动' },
  { value: 'startup', label: '启动时自动' },
  { value: 'scheduled', label: '定时刷新' },
]

const progressPct = computed(() => {
  const p = cacheProgress.value
  if (!p || !p.totalPages) return 0
  return Math.round((p.page / p.totalPages) * 100)
})

let pollTimer: ReturnType<typeof setInterval> | null = null

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(loadCacheStatus, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function loadCacheStatus() {
  try {
    const s = await getModelCacheStatus()
    cacheExists.value = s.exists
    cacheTotalCount.value = s.totalCount
    cacheFetchedAt.value = s.fetchedAt
    cacheRefreshing.value = s.refreshing
    cacheProgress.value = s.progress
    if (!s.refreshing) stopPolling()
  } catch { /* ignore */ }
}

async function handleRefreshCache() {
  try {
    const r = await refreshModelCache()
    if (r.ok) {
      cacheRefreshing.value = true
      cacheProgress.value = { page: 0, totalPages: null, count: 0 }
      startPolling()
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  // 若启动时后台正在刷新，自动接入轮询
  loadCacheStatus().then(() => { if (cacheRefreshing.value) startPolling() })
})
onBeforeUnmount(() => stopPolling())
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-2">
      <Icon icon="lucide:database" class="w-3.5 h-3.5 text-blue-400 shrink-0" />
      <span class="text-xs font-bold text-gray-300">模型缓存</span>
    </div>

    <!-- 缓存状态行 -->
    <div class="flex items-center gap-2 text-xs mb-2">
      <Icon
        :icon="cacheRefreshing ? 'lucide:loader-2' : cacheExists ? 'lucide:check-circle' : 'lucide:alert-circle'"
        class="w-3.5 h-3.5 shrink-0"
        :class="[
          cacheRefreshing ? 'text-blue-400 animate-spin' :
          cacheExists ? 'text-green-400' : 'text-yellow-500'
        ]"
      />
      <span v-if="cacheRefreshing && cacheProgress" class="text-blue-300">
        刷新中…
        <span v-if="cacheProgress.totalPages">
          第 <span class="text-white font-medium">{{ cacheProgress.page }}</span>/{{ cacheProgress.totalPages }} 页，
        </span>
        已获取 <span class="text-white font-medium">{{ cacheProgress.count }}</span> 个模型
      </span>
      <span v-else-if="cacheRefreshing" class="text-blue-300">后台刷新启动中…</span>
      <span v-else-if="cacheExists" class="text-gray-400">
        已缓存 <span class="text-gray-200 font-medium">{{ cacheTotalCount }}</span> 个模型
        <span v-if="cacheFetchedAt" class="text-gray-500 ml-1">
          · {{ new Date(cacheFetchedAt).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) }}
        </span>
      </span>
      <span v-else class="text-yellow-500">未初始化，请点击刷新</span>
    </div>

    <!-- 进度条（刷新中可见） -->
    <div v-if="cacheRefreshing" class="mb-2">
      <div class="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
        <div
          class="h-full bg-blue-500 rounded-full transition-all duration-500"
          :style="{ width: (progressPct || 5) + '%' }"
        />
      </div>
      <div class="text-right text-[10px] text-gray-500 mt-0.5">{{ progressPct }}%</div>
    </div>

    <!-- 刷新策略 -->
    <div class="flex items-center gap-2 mb-2">
      <span class="text-xs text-gray-400 w-16 shrink-0">刷新策略</span>
      <a-select
        v-model="cacheStrategy"
        :options="strategyOptions"
        size="small"
        class="w-32"
        @change="saveRHConfig({ model_cache_strategy: cacheStrategy })"
      />
    </div>

    <!-- 刷新按钮 -->
    <div class="flex justify-end">
      <a-button size="small" :disabled="cacheRefreshing" @click="handleRefreshCache">
        <template #icon>
          <Icon :icon="cacheRefreshing ? 'lucide:loader-2' : 'lucide:refresh-cw'" class="w-3 h-3" :class="cacheRefreshing ? 'animate-spin' : ''" />
        </template>
        {{ cacheRefreshing ? '刷新中…' : '立即刷新' }}
      </a-button>
    </div>
  </div>
</template>
