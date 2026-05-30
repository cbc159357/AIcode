/**
 * RunningHub 服务层 — 连接测试 / 工作流管理 / 任务调度 / 配置。
 */

import api from './api'

/** 图片输入语义角色 */
export type ImageInputRole = 'reference' | 'pose' | 'face' | 'style' | 'mask' | 'background' | 'internal'

/** 工作流图片输入标注 */
export interface ImageInput {
  nodeId: string
  fieldName: string
  role: ImageInputRole
  label: string
  required: boolean
  /** 运行时：上传后得到的 RH fileName，用于任务提交 */
  uploadedFileName?: string
}

/** 参数功能分组 */
export interface ParamGroup {
  groupId: string
  title: string
  defaultCollapsed: boolean
  nodeIds: string[]
}

/** 模型元数据（来自 RH 模型缓存） */
export interface ModelMeta {
  resourceType: string
  baseModel: string
  baseModelRaw: string
  resourceName: string
  quantization: string
  tags: string[]
  triggerWords: string
}

/** 模型搜索结果条目 */
export interface ModelSearchResult extends ModelMeta {
  filename: string
}

/** 工作流可调参数 */
export interface RHWorkflowParam {
  nodeId: string
  fieldName: string
  label: string
  nodeTitle?: string
  type: 'text' | 'number' | 'image' | 'select' | 'boolean'
  currentValue: string | number | boolean
  description: string
  priority: 'high' | 'medium' | 'low'
  constraints: Record<string, number>
  modelMeta?: ModelMeta
  /** 后端标记的模型类字段（含 name/path/ckpt/lora 关键词），即使无缓存元数据也为 true */
  isModelField?: boolean
}

/** 已保存的工作流摘要 */
export interface RHWorkflowItem {
  workflowId: string
  name: string
  description: string
  group: string
  fetchedAt: string
  paramCount: number
  nodeCount: number
  imageInputCount: number
  imageInputsAnnotated: boolean
}

/** 模型联动组（采样器 + 上游 Loader 节点） */
export interface ModelGroup {
  groupName: string
  samplerNodeId: string
  modelNodeIds: string[]
}

/** 已保存的工作流完整数据 */
export interface RHWorkflowDetail {
  workflowId: string
  name: string
  description: string
  group: string
  rawNodes: Record<string, unknown>
  analyzedParams: RHWorkflowParam[]
  imageInputs: ImageInput[]
  imageInputsAnnotated: boolean
  paramGroups?: ParamGroup[]
  modelGroups?: ModelGroup[]
  fetchedAt: string
}

/** RH 配置（脱敏） */
export interface RHConfig {
  active_key_type: string
  keys: Record<string, string>
  has_keys: Record<string, boolean>
  proxy: string
  proxy_enabled: boolean
}

/** 测试 API Key 连通性 */
export async function testConnection(apiKey: string): Promise<{ ok: boolean; message: string }> {
  const resp = await api.post('/rh/test', { api_key: apiKey })
  return resp.data
}

/** 获取工作流节点 JSON */
export async function fetchWorkflowJson(workflowId: string): Promise<{ ok: boolean; data: Record<string, unknown> | null; message: string }> {
  const resp = await api.post('/rh/workflow/fetch', { workflow_id: workflowId })
  return resp.data
}

/** 规则解析工作流可调参数 */
export async function analyzeWorkflow(workflowId: string, nodesJson?: Record<string, unknown>): Promise<{ ok: boolean; params: RHWorkflowParam[]; nodeCount: number; paramCount: number }> {
  const resp = await api.post('/rh/workflow/analyze', {
    workflow_id: workflowId,
    nodes_json: nodesJson ?? null,
  })
  return resp.data
}

/** 提交 RunningHub 任务 */
export async function createTask(workflowId: string, nodeInfoList?: { nodeId: string; fieldName: string; fieldValue: string }[]): Promise<{ ok: boolean; taskId: string; taskStatus: string; message: string }> {
  const resp = await api.post('/rh/task/create', {
    workflow_id: workflowId,
    node_info_list: nodeInfoList ?? null,
  })
  return resp.data
}

/** 查询任务状态 */
export async function pollTaskStatus(taskId: string): Promise<{ status: string; outputs: unknown[]; message: string }> {
  const resp = await api.post('/rh/task/status', { task_id: taskId })
  return resp.data
}

/** 取消任务 */
export async function cancelTask(taskId: string): Promise<{ ok: boolean; message: string }> {
  const resp = await api.post('/rh/task/cancel', { task_id: taskId })
  return resp.data
}

/** 获取本地已保存的工作流列表 */
export async function listSavedWorkflows(): Promise<{ ok: boolean; items: RHWorkflowItem[] }> {
  const resp = await api.get('/rh/workflows')
  return resp.data
}

/** 保存工作流配置 */
export async function saveWorkflow(data: {
  workflow_id: string
  name: string
  description?: string
  group?: string
  raw_nodes?: Record<string, unknown>
  analyzed_params?: RHWorkflowParam[]
}): Promise<{ ok: boolean; message: string }> {
  const resp = await api.post('/rh/workflow/save', data)
  return resp.data
}

/** 获取已保存的工作流详情 */
export async function getSavedWorkflow(workflowId: string): Promise<{ ok: boolean; data: RHWorkflowDetail }> {
  const resp = await api.get(`/rh/workflow/${workflowId}`)
  return resp.data
}

/** 删除工作流 */
export async function deleteWorkflow(workflowId: string): Promise<{ ok: boolean; message: string }> {
  const resp = await api.delete(`/rh/workflow/${workflowId}`)
  return resp.data
}

/** 获取 RH 配置（脱敏） */
export async function getRHConfig(): Promise<{ ok: boolean; config: RHConfig }> {
  const resp = await api.get('/rh/config')
  return resp.data
}

/** 保存 RH 配置 */
export async function saveRHConfig(data: {
  keys?: Record<string, string>
  active_key_type?: string
  proxy?: string
  proxy_enabled?: boolean
  model_cache_strategy?: string
  model_cache_interval_hours?: number
}): Promise<{ ok: boolean; message: string }> {
  const resp = await api.post('/rh/config/save', data)
  return resp.data
}

/** 将模型替换写回工作流 JSON（同步重新附加 modelMeta） */
export async function applyModelOverrides(
  workflowId: string,
  overrides: { nodeId: string; fieldName: string; value: string }[],
): Promise<{ ok: boolean; message: string }> {
  const resp = await api.patch(`/rh/workflows/${workflowId}/models`, overrides)
  return resp.data
}

/** 保存用户确认的图片输入标注 */
export async function updateImageInputs(
  workflowId: string,
  imageInputs: ImageInput[],
): Promise<{ ok: boolean; message: string }> {
  const resp = await api.put(`/rh/workflow/${workflowId}/image-inputs`, { image_inputs: imageInputs })
  return resp.data
}

/** 上传图片到 RunningHub，返回 fileName */
export async function uploadImageToRH(
  file: File,
): Promise<{ ok: boolean; fileName: string; message: string }> {
  const form = new FormData()
  form.append('file', file)
  const resp = await api.post('/rh/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return resp.data
}

export interface CacheProgress { page: number; totalPages: number | null; count: number }

/** 获取模型缓存状态 */
export async function getModelCacheStatus(): Promise<{
  exists: boolean; totalCount: number; fetchedAt: string | null
  refreshing: boolean; progress: CacheProgress | null
}> {
  const resp = await api.get('/rh/model-cache/status')
  return resp.data
}

/** 异步启动全量刷新（后台进行），立即返回 */
export async function refreshModelCache(): Promise<{ ok: boolean; message: string }> {
  const resp = await api.post('/rh/model-cache/refresh')
  return resp.data
}

/** 在缓存中搜索模型 */
export async function searchModels(params: {
  q?: string
  base_model?: string
  resource_type?: string
  limit?: number
}): Promise<ModelSearchResult[]> {
  const resp = await api.get('/rh/models/search', { params })
  return resp.data.items
}

/** 按文件名查询兼容候选列表 */
export async function suggestCompatibleModels(
  filename: string,
  resourceType?: string,
): Promise<{ sourceBaseModel: string | null; candidates: ModelSearchResult[] }> {
  const resp = await api.get('/rh/models/suggest', {
    params: { filename, resource_type: resourceType },
  })
  return resp.data
}

/** 参数 → nodeInfoList 转换（只传修改过的参数） */
export function buildNodeInfoList(
  params: RHWorkflowParam[],
  originalParams?: RHWorkflowParam[],
): { nodeId: string; fieldName: string; fieldValue: string }[] {
  const list: { nodeId: string; fieldName: string; fieldValue: string }[] = []
  for (let i = 0; i < params.length; i++) {
    const p = params[i]
    const orig = originalParams?.[i]
    if (orig && String(p.currentValue) === String(orig.currentValue)) continue
    if (p.fieldName === 'seed' && (p.currentValue === -1 || p.currentValue === '-1')) continue
    list.push({ nodeId: p.nodeId, fieldName: p.fieldName, fieldValue: String(p.currentValue) })
  }
  return list
}
