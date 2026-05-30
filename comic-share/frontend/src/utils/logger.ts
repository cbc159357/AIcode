/**
 * 日志工具模块 — 遵循 logging-standards.md 规范。
 *
 * - Development 模式: 全量输出 (DEBUG+)
 * - Production 模式: 仅 WARN + ERROR
 */

const isDev = import.meta.env.DEV

export const logger = {
  trace: (...args: unknown[]): void => {
    if (isDev) console.debug('[TRACE]', ...args)
  },

  debug: (...args: unknown[]): void => {
    if (isDev) console.debug('[DEBUG]', ...args)
  },

  info: (...args: unknown[]): void => {
    if (isDev) console.info('[INFO]', ...args)
  },

  warn: (...args: unknown[]): void => {
    console.warn('[WARN]', ...args)
  },

  error: (...args: unknown[]): void => {
    console.error('[ERROR]', ...args)
  },

  group: (label: string): void => {
    if (isDev) console.group(label)
  },

  groupEnd: (): void => {
    if (isDev) console.groupEnd()
  },

  time: (label: string): void => {
    if (isDev) console.time(label)
  },

  timeEnd: (label: string): void => {
    if (isDev) console.timeEnd(label)
  },

  table: (data: unknown): void => {
    if (isDev) console.table(data)
  },
}
