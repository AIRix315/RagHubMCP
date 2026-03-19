import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LatencyChart from '@/components/charts/LatencyChart.vue'
import type { BenchmarkResult } from '@/types/benchmark'

// Mock chart.js
vi.mock('chart.js', () => ({
  Chart: {
    register: vi.fn(),
  },
  CategoryScale: vi.fn(),
  LinearScale: vi.fn(),
  BarElement: vi.fn(),
  Title: vi.fn(),
  Tooltip: vi.fn(),
  Legend: vi.fn(),
}))

vi.mock('vue-chartjs', () => ({
  Bar: {
    name: 'Bar',
    template: '<div class="mock-bar-chart"></div>',
  },
}))

describe('LatencyChart', () => {
  const mockResults: BenchmarkResult[] = [
    {
      config_name: 'Fast Config',
      results: [],
      latency_ms: 50.0,
      embedding_provider: 'ollama',
      rerank_provider: null,
    },
    {
      config_name: 'Slow Config',
      results: [],
      latency_ms: 200.0,
      embedding_provider: 'ollama',
      rerank_provider: 'flashrank',
    },
    {
      config_name: 'Medium Config',
      results: [],
      latency_ms: 120.0,
      embedding_provider: 'openai',
      rerank_provider: null,
    },
  ]

  it('should render empty state when no results', () => {
    const wrapper = mount(LatencyChart, {
      props: { results: [] },
    })
    expect(wrapper.text()).toContain('暂无数据')
  })

  it('should render chart when results are provided', () => {
    const wrapper = mount(LatencyChart, {
      props: { results: mockResults },
    })
    expect(wrapper.find('.mock-bar-chart').exists()).toBe(true)
  })

  it('should handle single result', () => {
    const wrapper = mount(LatencyChart, {
      props: {
        results: [mockResults[0]],
      },
    })
    expect(wrapper.find('.mock-bar-chart').exists()).toBe(true)
  })
})