/**
 * 全局应用状态 — 服务状态、日志系统。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LogEntry, ServiceStatus } from '@/types'

export type SidebarMode = 'workspace' | 'tasks' | 'workflow' | 'settings'

export const useAppStore = defineStore('app', () => {
  // 侧栏模式
  const sidebarMode = ref<SidebarMode>('workspace')

  // 侧栏展开状态（默认展开）
  const sidebarExpanded = ref(true)

  // 预览抽屉
  const previewDrawerOpen = ref(false)

  // 服务状态
  const serviceStatus = ref<Record<string, ServiceStatus>>({
    comfyui: 'disconnected',
    cosyvoice: 'disconnected',
  })

  // 运行日志
  const logs = ref<LogEntry[]>([])

  // 进度
  const progressLabel = ref('')
  const progressPercent = ref(0)

  function log(level: LogEntry['level'], message: string) {
    logs.value.push({
      timestamp: Date.now(),
      level,
      message,
    })
    // 限制日志数量
    if (logs.value.length > 500) {
      logs.value = logs.value.slice(-300)
    }
  }

  function clearLogs() {
    logs.value = []
  }

  function updateProgress(label: string, percent: number) {
    progressLabel.value = label
    progressPercent.value = percent
  }

  function setServiceStatus(name: string, status: ServiceStatus) {
    serviceStatus.value[name] = status
  }

  return {
    sidebarMode,
    sidebarExpanded,
    previewDrawerOpen,
    serviceStatus,
    logs,
    progressLabel,
    progressPercent,
    log,
    clearLogs,
    updateProgress,
    setServiceStatus,
  }
})
