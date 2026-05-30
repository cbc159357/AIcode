/**
 * 服务状态检测 composable — 轮询外部服务健康状态。
 */

import { onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import api from '@/services/api'
import { logger } from '@/utils/logger'

const CHECK_INTERVAL = 30_000 // 30s

export function useServiceCheck() {
  const appStore = useAppStore()
  let timer: ReturnType<typeof setInterval> | null = null

  async function checkAll() {
    try {
      const resp = await api.get('/health')
      const services = resp.data.services || {}
      for (const [name, status] of Object.entries(services)) {
        appStore.setServiceStatus(name, status as 'connected' | 'disconnected')
      }
    } catch {
      logger.warn('健康检查失败')
    }
  }

  onMounted(() => {
    checkAll()
    timer = setInterval(checkAll, CHECK_INTERVAL)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  return { checkAll }
}
