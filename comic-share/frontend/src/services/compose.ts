/**
 * 合成/渲染服务 — 视频渲染 + 项目管理。
 */

import api from './api'
import type { Shot } from '@/types'

export interface RenderParams {
  project_name: string
  shots: Shot[]
  resolution?: string
  enable_subtitle?: boolean
  enable_bgm?: boolean
  bgm_path?: string | null
}

export async function saveProject(name: string, shots: Shot[]): Promise<string> {
  const resp = await api.post('/project/save', { project_name: name, shots })
  return resp.data.path
}

export async function renderVideo(params: RenderParams): Promise<string> {
  const resp = await api.post('/project/render', params)
  return resp.data.path
}

export async function getOutputUrl(filename: string): Promise<string> {
  return `${api.defaults.baseURL}/project/output/${filename}`
}

export async function exportProject(name: string, shots: Shot[]): Promise<Record<string, unknown>> {
  const resp = await api.post('/project/export', { project_name: name, shots })
  return resp.data
}

export async function importProject(data: Record<string, unknown>): Promise<{ project_name: string; shots: Shot[] }> {
  const resp = await api.post('/project/import', data)
  return resp.data
}
