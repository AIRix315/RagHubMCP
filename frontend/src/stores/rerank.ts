import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getRerankProviders } from '@/api'
import { getErrorMessage } from '@/api/errors'

/**
 * Rerank Provider 信息
 * 从后端 API 返回的 Provider 状态信息
 */
export interface RerankProvider {
  name: string
  type: 'onnx' | 'api' | 'hybrid' | 'vector'
  model: string
  status: 'active' | 'inactive' | 'error'
  config: {
    batch_size?: number
    max_length?: number
    score_threshold?: number
    device?: string
    rank_strategy?: string
  }
  is_default: boolean
  error_message?: string
}

export const useRerankStore = defineStore('rerank', () => {
  const providers = ref<RerankProvider[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * 从后端加载 Rerank Provider 列表
   * 使用真实 API 调用而非 mock 数据
   */
  async function loadProviders() {
    loading.value = true
    error.value = null
    try {
      const data = await getRerankProviders()
      // Transform API response to store format
      providers.value = data.map(p => ({
        name: p.name,
        type: p.type as RerankProvider['type'],
        model: p.model || '',
        status: p.status as RerankProvider['status'],
        config: (p.config || {}) as RerankProvider['config'],
        is_default: p.is_default,
        error_message: p.error_message,
      }))
    } catch (e) {
      error.value = getErrorMessage(e)
      console.error('Failed to load rerank providers:', e)
    } finally {
      loading.value = false
    }
  }

  /**
   * 清除 provider 列表
   */
  function clearProviders() {
    providers.value = []
    error.value = null
  }

  return {
    providers,
    loading,
    error,
    loadProviders,
    clearProviders,
  }
})