/** 全局类型定义 */

/** 单个分镜数据 */
export interface Shot {
  id: string
  index: number
  narration: string
  visual_prompt: string
  text: string
  animation?: string
  imageBlob?: Blob | null
  imagePath?: string
  videoBlob?: Blob | null
  video_prompt?: string
  audioBlob?: Blob | null
  audioDuration?: number
}

/** 角色数据 */
export interface Character {
  name: string
  tags: string
  description?: string
}

/** 项目状态 */
export interface ProjectState {
  projectName: string
  shots: Shot[]
  characters: Character[]
  currentStep: number
  bgmFile: File | null
  finalVideoUrl: string | null
  isRegenerating: boolean
  currentBatchFile: string | null
}

/** 服务连接状态 */
export type ServiceStatus = 'connected' | 'disconnected' | 'not_configured' | 'error'

/** 服务健康检查响应 */
export interface HealthResponse {
  status: string
  services: Record<string, ServiceStatus>
}

/** LLM 提供者配置 */
export interface LLMProvider {
  url: string
  need_key: boolean
  api_key?: string
  model?: string
}

/** 日志条目 */
export interface LogEntry {
  timestamp: number
  level: 'info' | 'success' | 'warn' | 'error'
  message: string
}

/** 进度更新 */
export interface ProgressUpdate {
  label: string
  percent: number
}

/** 归档 */
export interface Archive {
  id: string
  name: string
  created_at: string
  updated_at: string
  task_count: number
}

/** 子任务 */
export interface Task {
  id: string
  created_at: string
  status: 'running' | 'completed' | 'failed'
  pipeline_config: Record<string, string>
  media_count: Record<string, number>
}

/** 媒体资源项 */
export interface MediaItem {
  type: 'image' | 'audio' | 'video'
  filename: string
  path: string
  size: number
  duration?: number
}
