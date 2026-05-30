/**
 * 四步流水线调度 composable。
 */

import { ref, reactive } from 'vue'
import { useAppStore } from '@/stores/app'
import { useConfigStore } from '@/stores/config'
import { useProjectStore } from '@/stores/project'
import { generateStream } from '@/services/llm'
import { executeWorkflow, getTaskStatus } from '@/services/workflow'
import { synthesize } from '@/services/tts'
import { renderVideo } from '@/services/compose'
import type { Shot } from '@/types'

export type StepStatus = 'idle' | 'running' | 'done' | 'error'

export function usePipeline() {
  const appStore = useAppStore()
  const configStore = useConfigStore()
  const projectStore = useProjectStore()

  const stepStatuses = reactive<Record<number, StepStatus>>({
    1: 'idle', 2: 'idle', 3: 'idle', 4: 'idle',
  })
  const llmOutput = ref('')
  const isStreaming = ref(false)

  async function runStep1(storyText: string) {
    if (!storyText.trim()) {
      appStore.log('warn', '请先输入故事文本')
      return
    }

    stepStatuses[1] = 'running'
    llmOutput.value = ''
    isStreaming.value = true
    appStore.log('info', '步骤1: 开始生成剧本...')
    appStore.updateProgress('生成剧本', 0)

    try {
      await generateStream(
        {
          prompt: storyText,
          system_prompt: '你是一个漫画短片剧本作家。根据用户提供的故事文本，生成适合制作短视频的分镜剧本。每个分镜用 JSON 数组格式输出，包含 narration 和 visual_prompt 字段。',
          provider: configStore.llmProvider,
          model: configStore.llmModel || undefined,
          api_key: configStore.llmApiKey || undefined,
          temperature: configStore.llmTemperature,
          max_tokens: configStore.llmMaxTokens,
        },
        (chunk) => { llmOutput.value += chunk },
        (fullText) => {
          isStreaming.value = false
          stepStatuses[1] = 'done'
          appStore.updateProgress('生成剧本', 100)
          appStore.log('success', `步骤1 完成，共 ${fullText.length} 字`)
          parseShots(fullText)
        },
        (error) => {
          isStreaming.value = false
          stepStatuses[1] = 'error'
          appStore.updateProgress('', 0)
          appStore.log('error', `步骤1 失败: ${error}`)
        },
      )
    } catch (e) {
      isStreaming.value = false
      stepStatuses[1] = 'error'
      appStore.log('error', `步骤1 异常: ${e}`)
    }
  }

  function parseShots(text: string) {
    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]) as Array<Record<string, string>>
        const shots: Shot[] = parsed.map((item, i) => ({
          id: `shot_${i}`,
          index: i,
          narration: item.narration || item.text || '',
          visual_prompt: item.visual_prompt || item.prompt || '',
          text: item.narration || item.text || '',
        }))
        projectStore.setShots(shots)
        appStore.log('info', `解析出 ${shots.length} 个分镜`)
      }
    } catch {
      appStore.log('warn', '剧本 JSON 解析失败，请手动编辑')
    }
  }

  async function runStep2() {
    const shots = projectStore.shots
    if (!shots.length) {
      appStore.log('warn', '无分镜可生成图片')
      return
    }

    stepStatuses[2] = 'running'
    appStore.log('info', `步骤2: 生成 ${shots.length} 张图片...`)

    const [width, height] = configStore.imageSize.split('x').map(Number)
    let completed = 0

    for (const shot of shots) {
      appStore.updateProgress('生成图片', Math.round((completed / shots.length) * 100))

      try {
        const result = await executeWorkflow(
          configStore.activeEngine,
          shot.visual_prompt,
          width,
          height,
        )
        // 统一轮询
        let status = await getTaskStatus(result.task_id, result.engine)
        let tries = 0
        while (status.status === 'running' && tries < 120) {
          await new Promise(r => setTimeout(r, 3000))
          status = await getTaskStatus(result.task_id, result.engine)
          tries++
        }
        if (status.status === 'completed' && status.output?.length) {
          shot.imagePath = status.output[0]
        }
      } catch (e) {
        appStore.log('warn', `分镜 ${shot.index + 1} 生图失败: ${e}`)
      }
      completed++
    }

    projectStore.setShots([...shots])
    appStore.updateProgress('生成图片', 100)
    stepStatuses[2] = 'done'
    appStore.log('success', `步骤2 完成，${completed}/${shots.length} 张`)
  }

  async function runStep3() {
    const shots = projectStore.shots
    if (!shots.length) {
      appStore.log('warn', '无分镜可合成语音')
      return
    }

    stepStatuses[3] = 'running'
    appStore.log('info', `步骤3: 合成 ${shots.length} 段语音...`)
    let completed = 0

    for (const shot of shots) {
      appStore.updateProgress('语音合成', Math.round((completed / shots.length) * 100))
      if (!shot.narration) { completed++; continue }

      try {
        const blob = await synthesize(shot.narration, configStore.ttsRefAudio, configStore.ttsSpeed)
        shot.audioBlob = blob
        shot.audioDuration = blob.size / 32000 // 粗略估算
      } catch (e) {
        appStore.log('warn', `分镜 ${shot.index + 1} TTS 失败: ${e}`)
      }
      completed++
    }

    projectStore.setShots([...shots])
    appStore.updateProgress('语音合成', 100)
    stepStatuses[3] = 'done'
    appStore.log('success', `步骤3 完成`)
  }

  async function runStep4() {
    const shots = projectStore.shots
    stepStatuses[4] = 'running'
    appStore.log('info', '步骤4: 渲染视频...')
    appStore.updateProgress('渲染视频', 30)

    try {
      const path = await renderVideo({
        project_name: projectStore.projectName || 'untitled',
        shots,
        resolution: configStore.imageSize,
        enable_subtitle: configStore.enableSubtitle,
        enable_bgm: configStore.enableBgm,
      })
      appStore.updateProgress('渲染视频', 100)
      stepStatuses[4] = 'done'
      appStore.log('success', `步骤4 完成: ${path}`)
      projectStore.setFinalVideo(path)
    } catch (e) {
      stepStatuses[4] = 'error'
      appStore.log('error', `步骤4 失败: ${e}`)
    }
  }

  async function runStep(step: number, storyText?: string) {
    switch (step) {
      case 1: await runStep1(storyText || ''); break
      case 2: await runStep2(); break
      case 3: await runStep3(); break
      case 4: await runStep4(); break
    }
  }

  return {
    stepStatuses,
    llmOutput,
    isStreaming,
    runStep,
  }
}
