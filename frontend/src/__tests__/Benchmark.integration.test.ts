import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import Benchmark from '../views/Benchmark.vue'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  }),
  createI18n: () => ({})
}))

// Mock the API module
vi.mock('@/api/benchmark', () => ({
  runBenchmark: vi.fn()
}))

import { runBenchmark } from '@/api/benchmark'

describe('Benchmark API Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should call API when run button clicked', async () => {
    const mockResponse = {
      query: 'test query',
      collection: 'test-collection',
      total_latency_ms: 150,
      results: [
        {
          config_name: 'FlashRank + Hybrid',
          embedding_provider: 'ollama-bge',
          rerank_provider: 'flashrank-tiny',
          latency_ms: 45,
          results: [
            { id: '1', content: 'doc1', score: 0.9, rerank_score: 0.85 }
          ]
        }
      ]
    }
    
    vi.mocked(runBenchmark).mockResolvedValue(mockResponse)
    
    const wrapper = mount(Benchmark)
    
    await wrapper.find('[data-testid="run-benchmark"]').trigger('click')
    
    expect(runBenchmark).toHaveBeenCalled()
  })

  it('should update results after API call', async () => {
    const mockResponse = {
      query: 'test query',
      collection: 'test-collection',
      total_latency_ms: 150,
      results: [
        {
          config_name: 'Fast Config',
          embedding_provider: 'ollama-bge',
          rerank_provider: null,
          latency_ms: 30,
          results: []
        },
        {
          config_name: 'Balanced Config',
          embedding_provider: 'ollama-bge',
          rerank_provider: 'flashrank-tiny',
          latency_ms: 80,
          results: []
        }
      ]
    }
    
    vi.mocked(runBenchmark).mockResolvedValue(mockResponse)
    
    const wrapper = mount(Benchmark)
    await wrapper.find('[data-testid="run-benchmark"]').trigger('click')
    
    // Wait for the API call to complete
    await wrapper.vm.$nextTick()
    
    // Check that results were updated
    const vm = wrapper.vm as any
    expect(vm.benchmarkResults.length).toBe(2)
    expect(vm.benchmarkResults[0].config_name).toBe('Fast Config')
  })

  it('should handle API error gracefully', async () => {
    vi.mocked(runBenchmark).mockRejectedValue(new Error('API Error'))
    
    const wrapper = mount(Benchmark)
    
    // Should not throw
    await wrapper.find('[data-testid="run-benchmark"]').trigger('click')
    
    // Loading should be reset even on error
    await wrapper.vm.$nextTick()
    const vm = wrapper.vm as any
    expect(vm.loading).toBe(false)
  })
})