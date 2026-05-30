/**
 * 常量定义 — 风格预设、时代预设、图片尺寸等。
 */

/** 风格预设 */
export const STYLE_PRESETS = [
  { label: '二次元/动漫', value: 'anime' },
  { label: '写实摄影', value: 'photorealistic' },
  { label: '水墨国风', value: 'chinese_ink' },
  { label: '赛博朋克', value: 'cyberpunk' },
  { label: '油画风', value: 'oil_painting' },
] as const

/** 时代背景预设 */
export const ERA_PRESETS = [
  { label: '现代', value: 'modern' },
  { label: '未来', value: 'future' },
  { label: '古代', value: 'ancient' },
  { label: '中世纪', value: 'medieval' },
  { label: '民国', value: 'republic' },
] as const

/** 图片尺寸选项 */
export const IMAGE_SIZES = [
  { label: '竖版 (720×1280)', value: '720x1280' },
  { label: '横版 (1280×720)', value: '1280x720' },
  { label: '方形 (1024×1024)', value: '1024x1024' },
] as const

// T2I_MODELS 和 IMAGE_ENGINE_MODES 已迁移到后端 config.yaml workflows.registry
// 前端通过 GET /api/v1/workflow/list 获取工作流列表
