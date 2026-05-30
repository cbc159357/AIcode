/**
 * 项目状态 — 管理分镜、角色、项目数据。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Character, Shot } from '@/types'

export const useProjectStore = defineStore('project', () => {
  const projectName = ref('')
  const shots = ref<Shot[]>([])
  const characters = ref<Character[]>([])
  const currentStep = ref(0)
  const finalVideoUrl = ref<string | null>(null)
  const isRegenerating = ref(false)
  const currentBatchFile = ref<string | null>(null)

  function resetState() {
    shots.value = []
    characters.value = []
    currentStep.value = 0
    finalVideoUrl.value = null
    isRegenerating.value = false
    currentBatchFile.value = null
  }

  function setProjectName(name: string) {
    projectName.value = name
  }

  function setShots(newShots: Shot[]) {
    shots.value = newShots
  }

  function addShot(shot: Shot) {
    shots.value.push(shot)
  }

  function updateShot(index: number, data: Partial<Shot>) {
    if (shots.value[index]) {
      Object.assign(shots.value[index], data)
    }
  }

  function setFinalVideo(url: string) {
    finalVideoUrl.value = url
  }

  return {
    projectName,
    shots,
    characters,
    currentStep,
    finalVideoUrl,
    isRegenerating,
    currentBatchFile,
    resetState,
    setProjectName,
    setShots,
    addShot,
    updateShot,
    setFinalVideo,
  }
})
