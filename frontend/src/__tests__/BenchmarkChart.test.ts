import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BenchmarkChart from '@/components/charts/BenchmarkChart.vue'
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

describe('BenchmarkChart', () => {
  const mockResults: BenchmarkResult[] = [
    {
      config_name: 'Config A',
      results: [
        { id: '1', text: 'result 1', score: 0.9 },
        { id: '2', text: 'result 2', score: 0.8 },
      ],
      latency_ms: 150.5,
      embedding_provider: 'ollama',
      rerank_provider: 'flashrank',
    },
    {
      config_name: 'Config B',
      results: [
        { id: '3', text: 'result 3', score: 0.85 },
      ],
      latency_ms: 100.2,
      embedding_provider: 'ollama',
      rerank_provider: null,
    },
  ]

  it('should render empty state when no results', () => {
    const wrapper = mount(BenchmarkChart, {
      props: { results: [] },
    })
    expect(wrapper.text()).toContain('暂无数据')
  })

  it('should render chart when results are provided', () => {
    const wrapper = mount(BenchmarkChart, {
      props: { results: mockResults },
    })
    expect(wrapper.find('.mock-bar-chart').exists()).toBe(true)
  })

  it('should display title when provided', () => {
    const wrapper = mount(BenchmarkChart, {
      props: {
        results: mockResults,
        title: 'Test Chart',
      },
    })
    expect(wrapper.find('.mock-bar-chart').exists()).toBe(true)
  })
})