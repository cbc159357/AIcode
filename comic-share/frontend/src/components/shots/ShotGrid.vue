<script setup lang="ts">
import type { Shot } from '@/types'
import ShotCard from './ShotCard.vue'

defineProps<{
  shots: Shot[]
}>()

const emit = defineEmits<{
  editShot: [shot: Shot]
  regenerateShot: [shot: Shot]
}>()
</script>

<template>
  <div class="h-full overflow-y-auto p-4">
    <div v-if="shots.length" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
      <ShotCard
        v-for="shot in shots"
        :key="shot.id"
        :shot="shot"
        @edit="emit('editShot', shot)"
        @regenerate="emit('regenerateShot', shot)"
      />
    </div>
    <div v-else class="flex items-center justify-center h-full text-gray-500">
      <p>完成步骤1后，分镜将在此显示</p>
    </div>
  </div>
</template>
