<script setup lang="ts">
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { Icon } from '@iconify/vue'
import { searchModels, type ModelSearchResult } from '@/services/runninghub'
import { archBadgeClass } from '@/utils/modelArchColors'

const props = defineProps<{
  modelValue: string
  resourceType: string
  targetBaseModel?: string
  incompatible?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
  (e: 'select', item: ModelSearchResult): void
}>()


const inputVal = ref(props.modelValue)
const isOpen = ref(false)
const candidates = ref<ModelSearchResult[]>([])
const searchQuery = ref('')
const loading = ref(false)
const searchRef = ref<HTMLInputElement | null>(null)
const wrapRef = ref<HTMLDivElement | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function archBadge(baseModel: string) { return archBadgeClass(baseModel) }

const displayedCandidates = computed(() =>
  candidates.value.filter(c => c.filename !== inputVal.value)
)

async function loadCandidates(q?: string) {
  if (!props.targetBaseModel) return
  loading.value = true
  try {
    candidates.value = await searchModels({
      base_model: props.targetBaseModel,
      resource_type: props.resourceType || undefined,
      q: q || undefined,
      limit: 30,
    })
  } catch { /* ignore */ } finally {
    loading.value = false
  }
}

function openDropdown() {
  isOpen.value = true
  if (!candidates.value.length) loadCandidates()
  setTimeout(() => searchRef.value?.focus(), 50)
}

function onSearchInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => loadCandidates(searchQuery.value), 300)
}

function selectCandidate(item: ModelSearchResult) {
  inputVal.value = item.filename
  emit('update:modelValue', item.filename)
  emit('select', item)
  isOpen.value = false
  searchQuery.value = ''
}

function onMainBlur(e: FocusEvent) {
  const rel = e.relatedTarget as HTMLElement | null
  if (wrapRef.value?.contains(rel)) return
  if (!props.incompatible) isOpen.value = false
  emit('update:modelValue', inputVal.value)
}

function onOutsideClick(e: MouseEvent) {
  if (!wrapRef.value?.contains(e.target as Node)) {
    isOpen.value = false
  }
}

watch(() => props.modelValue, v => { inputVal.value = v })

watch(() => props.incompatible, v => {
  if (v) openDropdown()
})

watch(() => props.targetBaseModel, () => {
  candidates.value = []
  if (isOpen.value) loadCandidates(searchQuery.value)
})

onMounted(() => {
  document.addEventListener('mousedown', onOutsideClick)
  if (props.incompatible) openDropdown()
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onOutsideClick)
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<template>
  <div ref="wrapRef" class="relative w-full">
    <!-- 主输入框 -->
    <input
      v-model="inputVal"
      class="w-full bg-gray-700/60 border rounded px-2 py-1 text-xs text-gray-200 outline-none transition-colors"
      :class="incompatible
        ? 'border-red-500/70 focus:border-red-400'
        : 'border-gray-600 focus:border-blue-500/60'"
      placeholder="模型文件名"
      @focus="openDropdown"
      @blur="onMainBlur"
    />

    <!-- 下拉候选面板 -->
    <div
      v-if="isOpen"
      class="absolute z-50 top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded shadow-xl max-h-52 flex flex-col"
    >
      <!-- 搜索框 -->
      <div class="p-1.5 border-b border-gray-700 shrink-0">
        <div class="flex items-center gap-1.5 bg-gray-700/60 rounded px-2 py-1">
          <Icon icon="lucide:search" class="w-3 h-3 text-gray-500 shrink-0" />
          <input
            ref="searchRef"
            v-model="searchQuery"
            class="flex-1 bg-transparent text-xs text-gray-200 outline-none placeholder-gray-500"
            :placeholder="targetBaseModel ? `搜索 ${targetBaseModel} 兼容模型...` : '搜索模型...'"
            @input="onSearchInput"
          />
          <Icon v-if="loading" icon="lucide:loader-2" class="w-3 h-3 text-gray-400 animate-spin shrink-0" />
        </div>
      </div>

      <!-- 候选列表 -->
      <div class="overflow-y-auto flex-1">
        <div v-if="!displayedCandidates.length && !loading" class="px-3 py-4 text-xs text-gray-500 text-center">
          {{ targetBaseModel ? `未找到 ${targetBaseModel} 兼容模型` : '无缓存数据' }}
        </div>
        <button
          v-for="item in displayedCandidates"
          :key="item.filename"
          class="w-full text-left px-2.5 py-1.5 hover:bg-gray-700/60 flex items-start gap-2 group"
          @mousedown.prevent="selectCandidate(item)"
        >
          <span
            class="mt-0.5 shrink-0 text-[9px] px-1 py-0.5 rounded border font-mono"
            :class="archBadge(item.baseModel)"
          >{{ item.baseModel }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-xs text-gray-200 truncate leading-tight">{{ item.resourceName || item.filename }}</div>
            <div class="text-[10px] text-gray-500 truncate flex items-center gap-1.5">
              <span class="truncate">{{ item.filename }}</span>
              <span class="shrink-0 text-gray-600 bg-gray-700/60 px-1 rounded">{{ item.quantization }}</span>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
