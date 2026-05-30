/**
 * 归档管理服务 — 归档 CRUD + 子任务 + 媒体查询。
 */

import api from './api'
import type { Archive, Task, MediaItem } from '@/types'

/** 列出所有归档 */
export async function listArchives(): Promise<Archive[]> {
  const resp = await api.get('/archives')
  return resp.data.archives
}

/** 新建归档 */
export async function createArchive(name: string): Promise<Archive> {
  const resp = await api.post('/archives', { name })
  return resp.data
}

/** 重命名归档 */
export async function renameArchive(id: string, name: string): Promise<void> {
  await api.put(`/archives/${id}`, { name })
}

/** 删除归档 */
export async function deleteArchive(id: string): Promise<void> {
  await api.delete(`/archives/${id}`)
}

/** 列出归档下所有子任务 */
export async function listTasks(archiveId: string): Promise<Task[]> {
  const resp = await api.get(`/archives/${archiveId}/tasks`)
  return resp.data.tasks
}

/** 创建子任务 */
export async function createTask(archiveId: string, pipelineConfig?: Record<string, string>): Promise<Task> {
  const resp = await api.post(`/archives/${archiveId}/tasks`, { pipeline_config: pipelineConfig })
  return resp.data
}

/** 更新子任务状态 */
export async function updateTaskStatus(archiveId: string, taskId: string, status: string): Promise<void> {
  await api.put(`/archives/${archiveId}/tasks/${taskId}/status`, { status })
}

/** 删除子任务 */
export async function deleteTask(archiveId: string, taskId: string): Promise<void> {
  await api.delete(`/archives/${archiveId}/tasks/${taskId}`)
}

/** 列出子任务下所有媒体 */
export async function listMedia(archiveId: string, taskId: string): Promise<MediaItem[]> {
  const resp = await api.get(`/archives/${archiveId}/tasks/${taskId}/media`)
  return resp.data.media
}

/** 获取媒体文件完整 URL */
export function getMediaUrl(path: string): string {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/api/v1/archives/media/${path}`
}
