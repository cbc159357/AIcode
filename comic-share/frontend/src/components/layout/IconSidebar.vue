<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const items = [
  { name: 'workspace', path: '/workspace', icon: 'lucide:layout-dashboard', label: '工作台' },
  { name: 'tasks', path: '/tasks', icon: 'lucide:folder-archive', label: '任务' },
  { name: 'workflow', path: '/workflow', icon: 'lucide:git-branch', label: '工作流' },
  { name: 'settings', path: '/settings', icon: 'lucide:settings', label: '设置' },
]

function isActive(item: typeof items[number]) {
  return route.path === item.path || route.path.startsWith(item.path + '/')
}
</script>

<template>
  <aside
    class="bg-gray-900 border-r border-gray-700 flex flex-col py-4 gap-2 transition-all duration-200 shrink-0"
    :class="appStore.sidebarExpanded ? 'w-48 px-3' : 'w-14 items-center'"
  >
    <!-- 导航项 -->
    <router-link
      v-for="item in items"
      :key="item.name"
      :to="item.path"
      class="rounded-lg flex items-center gap-3 transition-all"
      :class="[
        isActive(item)
          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
          : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800',
        appStore.sidebarExpanded ? 'px-3 py-2' : 'w-10 h-10 justify-center mx-auto',
      ]"
      :title="appStore.sidebarExpanded ? undefined : item.label"
    >
      <Icon :icon="item.icon" class="w-5 h-5 shrink-0" />
      <span v-if="appStore.sidebarExpanded" class="text-sm">{{ item.label }}</span>
    </router-link>

    <div class="flex-1" />

    <!-- 收起/展开按钮 -->
    <button
      class="rounded-lg flex items-center gap-3 text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-all"
      :class="appStore.sidebarExpanded ? 'px-3 py-2' : 'w-10 h-10 justify-center mx-auto'"
      :title="appStore.sidebarExpanded ? '收起侧栏' : '展开侧栏'"
      @click="appStore.sidebarExpanded = !appStore.sidebarExpanded"
    >
      <Icon
        :icon="appStore.sidebarExpanded ? 'lucide:panel-left-close' : 'lucide:panel-left-open'"
        class="w-5 h-5 shrink-0"
      />
      <span v-if="appStore.sidebarExpanded" class="text-sm">收起</span>
    </button>
  </aside>
</template>
