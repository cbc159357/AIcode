/**
 * 工作流服务 — 统一 API 调用层。
 * 前端不包含任何引擎细节（节点映射、replacements 等）。
 */

import api from './api'

/** 引擎模式项 */
export interface EngineItem {
  id: string
  name: string
  description: string
  has_workflow: boolean
}

/** 引擎列表响应 */
export interface EngineListResponse {
  engines: EngineItem[]
  default: string
}

/** 工作流列表项（API 返回结构） */
export interface WorkflowItem {
  id: string
  name: string
  category: string
  engine: string
  default_size: string
  description: string
}

/** 列表响应 */
export interface WorkflowListResponse {
  workflows: WorkflowItem[]
  default: string
}

/** 执行响应 */
export interface ExecuteResponse {
  task_id: string
  engine: string
}

/** 任务状态响应（归一化） */
export interface TaskStatusResponse {
  status: 'running' | 'completed' | 'failed' | 'error'
  progress?: number
  output?: string[]
  error?: string
}

/** 获取引擎模式列表（下拉框用） */
export async function listEngines(): Promise<EngineListResponse> {
  const resp = await api.get('/workflow/engines')
  return resp.data
}

/** 获取已启用的工作流列表 */
export async function listWorkflows(category?: string): Promise<WorkflowListResponse> {
  const resp = await api.get('/workflow/list', { params: category ? { category } : {} })
  return resp.data
}

/** 获取默认工作流 ID */
export async function getActiveWorkflowId(): Promise<string> {
  const resp = await api.get('/workflow/active')
  return resp.data.workflow_id
}

/** 执行工作流（统一入口，按引擎模式执行） */
export async function executeWorkflow(
  engine: string,
  prompt: string,
  width: number,
  height: number,
): Promise<ExecuteResponse> {
  const resp = await api.post('/workflow/execute', {
    engine,
    prompt,
    width,
    height,
  })
  return resp.data
}

/** 查询任务状态（统一入口） */
export async function getTaskStatus(taskId: string, engine: string): Promise<TaskStatusResponse> {
  const resp = await api.get('/workflow/task/status', { params: { task_id: taskId, engine } })
  return resp.data
}
