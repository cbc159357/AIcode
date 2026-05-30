<script setup lang="ts">
import RHKeyConfig from '@/components/settings/RHKeyConfig.vue'
import ModelCachePanel from '@/components/settings/ModelCachePanel.vue'
</script>

<template>
  <div class="space-y-3">
    <!-- API Key + 代理配置 -->
    <RHKeyConfig />
    <!-- 模型缓存管理（独立关注点） -->
    <div class="border-t border-gray-700/60 pt-3 mt-1">
      <ModelCachePanel />
    </div>
  </div>
</template>
