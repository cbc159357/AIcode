/**
 * 模型架构族配色映射 — 所有需要展示架构徽章的组件统一从此导入。
 * 新增架构只需改这一处。
 */
export const ARCH_COLORS: Record<string, string> = {
  'Flux2-Klein': 'bg-violet-600/20 text-violet-300 border-violet-500/40',
  'Flux1':       'bg-blue-600/20  text-blue-300  border-blue-500/40',
  'SDXL':        'bg-orange-600/20 text-orange-300 border-orange-500/40',
  'SD15':        'bg-green-600/20  text-green-300  border-green-500/40',
  'HiDream':     'bg-pink-600/20   text-pink-300   border-pink-500/40',
  'Wan2':        'bg-teal-600/20   text-teal-300   border-teal-500/40',
}

export function archBadgeClass(baseModel: string | undefined): string {
  if (!baseModel) return 'bg-gray-600/20 text-gray-400 border-gray-600/40'
  return ARCH_COLORS[baseModel] ?? 'bg-gray-600/20 text-gray-400 border-gray-600/40'
}
