/**
 * ComfyUI 服务 — 后端代理调用。
 */

import api from './api'

export interface WorkflowInfo {
  id: string
  name: string
  path: string
}

export interface ExecuteResult {
  prompt_id: string
  client_id: string
  status: string
}

export interface TaskStatus {
  status: 'running' | 'completed' | 'error' | 'unknown'
  outputs?: Record<string, unknown>
  error?: string
}

export async function checkHealth(): Promise<boolean> {
  const resp = await api.get('/comfyui/health')
  return resp.data.status === 'connected'
}

export async function listWorkflows(): Promise<WorkflowInfo[]> {
  const resp = await api.get('/comfyui/workflows')
  return resp.data.workflows
}

export async function executeWorkflow(
  workflowId: string,
  replacements?: Record<string, string>,
): Promise<ExecuteResult> {
  const resp = await api.post('/comfyui/execute', {
    workflow_id: workflowId,
    replacements,
  })
  return resp.data
}

export async function getTaskStatus(promptId: string): Promise<TaskStatus> {
  const resp = await api.get(`/comfyui/status/${promptId}`)
  return resp.data
}

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const resp = await api.post('/comfyui/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return resp.data.filename
}
