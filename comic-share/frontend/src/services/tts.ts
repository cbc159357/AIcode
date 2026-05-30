/**
 * TTS 服务 — CosyVoice 后端代理。
 */

import api from './api'

export interface RefAudio {
  name: string
  path: string
}

export async function checkHealth(): Promise<boolean> {
  const resp = await api.get('/tts/health')
  return resp.data.status === 'connected'
}

export async function listRefAudios(): Promise<RefAudio[]> {
  const resp = await api.get('/tts/audios')
  return resp.data.audios
}

export async function synthesize(
  text: string,
  refAudio?: string,
  speed?: number,
): Promise<Blob> {
  const resp = await api.post(
    '/tts/synthesize',
    { text, ref_audio: refAudio || '', speed: speed || 1.0 },
    { responseType: 'blob' },
  )
  return resp.data
}
