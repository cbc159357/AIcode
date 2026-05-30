<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { name: 'workflow-library', path: '/workflow/library', icon: 'lucide:git-branch', label: '工作流库' },
  { name: 'workflow-model-check', path: '/workflow/model-check', icon: 'lucide:flask-conical', label: '模型兼容检测' },
]
</script>

<template>
  <div class="h-full flex flex-col bg-gray-900">
    <!-- 子导航 Tab -->
    <div class="flex items-center gap-1 px-4 pt-3 pb-0 border-b border-gray-700 shrink-0">
      <router-link
        v-for="tab in tabs"
        :key="tab.name"
        :to="tab.path"
        class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-t transition-colors border-b-2 -mb-px"
        :class="route.name === tab.name
          ? 'text-blue-400 border-blue-500 bg-blue-500/10'
          : 'text-gray-400 border-transparent hover:text-gray-200'"
      >
        <Icon :icon="tab.icon" class="w-3.5 h-3.5" />
        {{ tab.label }}
      </router-link>
    </div>

    <!-- 子路由内容 -->
    <div class="flex-1 overflow-hidden">
      <router-view />
    </div>
  </div>
</template>
