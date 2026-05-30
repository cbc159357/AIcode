/**
 * 模型架构兼容性判断 — 统一 ParamGroup（工作流编辑器）与 ModelChecker（模型检测器）两处逻辑。
 *
 * 以「多数投票」确定权威架构族（dominantBaseModel），再据此判定每个参数是否兼容。
 * LoRA 为附加增强，不强制架构一致，故始终视为兼容。
 */
import { computed, type Ref } from 'vue'
import type { RHWorkflowParam } from '@/services/runninghub'

export type CompatStatus = 'ok' | 'warn' | 'err'

export function useModelCompat(params: Ref<RHWorkflowParam[]>) {
  /** 多数投票：出现次数最多的 baseModel 即权威架构族 */
  const dominantBaseModel = computed<string | undefined>(() => {
    const bases = params.value
      .filter(p => p.modelMeta?.baseModel)
      .map(p => p.modelMeta!.baseModel)
    if (!bases.length) return undefined
    return [...bases].sort(
      (a, b) =>
        bases.filter(x => x === b).length - bases.filter(x => x === a).length,
    )[0]
  })

  /** 单参数兼容状态：无元数据→warn，无主模型/LoRA→ok，架构不一致→err */
  function compatStatus(param: RHWorkflowParam): CompatStatus {
    if (!param.modelMeta) return 'warn'
    if (!dominantBaseModel.value) return 'ok'
    if (param.modelMeta.resourceType === 'LORA') return 'ok'
    return param.modelMeta.baseModel !== dominantBaseModel.value ? 'err' : 'ok'
  }

  /** 是否与主模型架构冲突（warn 不算冲突） */
  function isIncompatible(param: RHWorkflowParam): boolean {
    return compatStatus(param) === 'err'
  }

  return { dominantBaseModel, compatStatus, isIncompatible }
}
