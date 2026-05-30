/**
 * Axios 实例 — 统一 API 请求配置。
 */

import axios from 'axios'
import { logger } from '@/utils/logger'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 — 开发模式下记录请求
api.interceptors.request.use((config) => {
  logger.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

// 响应拦截器 — 开发模式下记录响应
api.interceptors.response.use(
  (response) => {
    logger.debug(`[API] ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    const status = error.response?.status || 'NETWORK'
    const url = error.config?.url || 'unknown'
    logger.error(`[API] ${status} ${url}:`, error.message)
    return Promise.reject(error)
  },
)

export default api
