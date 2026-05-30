<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useServiceCheck } from '@/composables/useServiceCheck'
import TopBar from '@/components/layout/TopBar.vue'
import IconSidebar from '@/components/layout/IconSidebar.vue'
import PreviewDrawer from '@/components/layout/PreviewDrawer.vue'

const appStore = useAppStore()

useServiceCheck()

onMounted(() => {
  appStore.log('info', 'comic-share v0.1.0 启动')
})
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-900 text-white">
    <!-- 顶部导航栏 -->
    <TopBar />

    <!-- 主体：侧栏 + 路由内容 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 左侧侧栏 -->
      <IconSidebar />

      <!-- 路由内容区 -->
      <main class="flex-1 overflow-hidden">
        <router-view />
      </main>
    </div>

    <!-- 右侧预览抽屉（默认收起） -->
    <PreviewDrawer v-model:open="appStore.previewDrawerOpen" />
  </div>
</template>
