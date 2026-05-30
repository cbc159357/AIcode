/**
 * LLM 服务 — SSE 流式调用。
 */

import { logger } from '@/utils/logger'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export interface LLMGenerateParams {
  prompt: string
  system_prompt?: string
  provider?: string
  model?: string
  api_key?: string
  temperature?: number
  max_tokens?: number
}

export interface LLMModel {
  id: string
  name: string
}

/**
 * 获取模型列表
 */
export async function fetchModels(provider?: string): Promise<LLMModel[]> {
  const resp = await fetch(`${API_BASE}/api/v1/llm/models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  })
  if (!resp.ok) throw new Error(`获取模型失败: ${resp.status}`)
  const data = await resp.json()
  return data.models || []
}

/**
 * 流式生成文本，回调接收每个 chunk
 */
export async function generateStream(
  params: LLMGenerateParams,
  onChunk: (text: string) => void,
  onDone?: (fullText: string) => void,
  onError?: (error: string) => void,
): Promise<void> {
  const resp = await fetch(`${API_BASE}/api/v1/llm/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })

  if (!resp.ok) {
    const errText = await resp.text()
    onError?.(errText)
    return
  }

  const reader = resp.body?.getReader()
  if (!reader) {
    onError?.('无法读取响应流')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          continue
        }
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6)
          try {
            const data = JSON.parse(jsonStr)
            if (data.content !== undefined) {
              onChunk(data.content)
            } else if (data.full_response !== undefined) {
              onDone?.(data.full_response)
            } else if (data.error !== undefined) {
              onError?.(data.error)
            }
          } catch {
            logger.debug('SSE JSON parse skip:', jsonStr)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
