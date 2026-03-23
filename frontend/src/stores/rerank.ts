import { defineStore } from 'pinia'
import { ref } from 'vue'

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
}

export const useRerankStore = defineStore('rerank', () => {
  const providers = ref<RerankProvider[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Mock data for development
  const mockProviders: RerankProvider[] = [
    {
      name: 'onnx-tiny',
      type: 'onnx',
      model: 'ms-marco-TinyBERT-L-2-v2',
      status: 'active',
      config: {
        batch_size: 32,
        max_length: 512,
        score_threshold: 0.3,
        device: 'CPU',
        rank_strategy: 'standard',
      },
      is_default: true,
    },
    {
      name: 'onnx-minilm',
      type: 'onnx',
      model: 'ms-marco-MiniLM-L-12-v2',
      status: 'inactive',
      config: {
        batch_size: 16,
        max_length: 512,
        score_threshold: 0.5,
        device: 'CPU',
        rank_strategy: 'diversity',
      },
      is_default: false,
    },
  ]

  async function loadProviders() {
    loading.value = true
    error.value = null
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500))
      providers.value = mockProviders
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load providers'
    } finally {
      loading.value = false
    }
  }

  async function testProvider(_name: string): Promise<{ latency_ms: number; success: boolean }> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 100))
    return { latency_ms: 45, success: true }
  }

  async function setDefault(name: string) {
    providers.value = providers.value.map((p) => ({
      ...p,
      is_default: p.name === name,
    }))
  }

  async function deleteProvider(name: string) {
    providers.value = providers.value.filter((p) => p.name !== name)
  }

  return {
    providers,
    loading,
    error,
    loadProviders,
    testProvider,
    setDefault,
    deleteProvider,
  }
})