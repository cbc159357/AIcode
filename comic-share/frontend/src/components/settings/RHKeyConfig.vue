<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { getRHConfig, saveRHConfig, testConnection } from '@/services/runninghub'

const apiKey = ref('')
const proxy = ref('')
const proxyEnabled = ref(false)
const activeKeyType = ref('consumer')
const hasKeys = ref<Record<string, boolean>>({})
const testing = ref(false)
const testResult = ref<{ ok: boolean; message: string } | null>(null)
const saving = ref(false)

const keyTypeOptions = [
  { value: 'consumer', label: '个人版' },
  { value: 'enterprise_shared', label: '企业共享版' },
]

const keyConfigured = computed(() => !!hasKeys.value[activeKeyType.value])
const keyPlaceholder = computed(() =>
  keyConfigured.value ? '已保存 · 输入新 Key 可覆盖' : '输入 API Key',
)

async function loadConfig() {
  try {
    const { config } = await getRHConfig()
    activeKeyType.value = config.active_key_type
    proxy.value = config.proxy
    proxyEnabled.value = config.proxy_enabled
    hasKeys.value = config.has_keys
  } catch { /* ignore */ }
}

async function handleTest() {
  if (!apiKey.value.trim()) return
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await testConnection(apiKey.value.trim())
  } catch {
    testResult.value = { ok: false, message: '请求失败' }
  } finally {
    testing.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      active_key_type: activeKeyType.value,
      proxy: proxy.value,
      proxy_enabled: proxyEnabled.value,
    }
    if (apiKey.value.trim()) {
      payload.keys = { [activeKeyType.value]: apiKey.value.trim() }
    }
    await saveRHConfig(payload as Parameters<typeof saveRHConfig>[0])
    await loadConfig()
    apiKey.value = ''
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<template>
  <div class="space-y-3">
    <!-- Key 类型 -->
    <div class="flex items-center gap-2">
      <span class="text-xs text-gray-400 w-16 shrink-0">Key 类型</span>
      <a-select v-model="activeKeyType" :options="keyTypeOptions" size="small" class="w-36" />
      <span v-if="hasKeys[activeKeyType]" class="text-xs text-green-400">已配置</span>
      <span v-else class="text-xs text-gray-500">未配置</span>
    </div>

    <!-- API Key 输入 -->
    <div class="flex items-center gap-2">
      <span class="text-xs text-gray-400 w-16 shrink-0">API Key</span>
      <div class="flex-1 relative">
        <a-input-password
          v-model="apiKey"
          size="small"
          :placeholder="keyPlaceholder"
        />
        <Icon
          v-if="keyConfigured && !apiKey"
          icon="lucide:shield-check"
          class="absolute right-8 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-green-400 pointer-events-none"
        />
      </div>
      <a-button size="small" :loading="testing" @click="handleTest">
        测试
      </a-button>
    </div>

    <!-- 测试结果 -->
    <div v-if="testResult" class="text-xs pl-18" :class="testResult.ok ? 'text-green-400' : 'text-red-400'">
      {{ testResult.message }}
    </div>

    <!-- 代理设置 -->
    <div class="flex items-center gap-2">
      <span class="text-xs text-gray-400 w-16 shrink-0">代理</span>
      <a-input v-model="proxy" size="small" class="flex-1" placeholder="http://127.0.0.1:7890" :disabled="!proxyEnabled" />
      <a-switch v-model="proxyEnabled" size="small" />
    </div>

    <!-- 保存按钮 -->
    <div class="flex justify-end">
      <a-button type="primary" size="small" :loading="saving" @click="handleSave">
        <template #icon><Icon icon="lucide:save" class="w-3 h-3" /></template>
        保存配置
      </a-button>
    </div>
  </div>
</template>
