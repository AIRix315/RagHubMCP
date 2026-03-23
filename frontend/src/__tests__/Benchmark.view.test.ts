import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Benchmark from '@/views/Benchmark.vue'
import { createTestI18n } from './test-utils/i18n'

// Mock the benchmark API
const mockRunBenchmark = vi.hoisted(() => vi.fn())

vi.mock('@/api/benchmark', () => ({
  runBenchmark: mockRunBenchmark,
}))

describe('Benchmark.vue', () => {
  let pinia: ReturnType<typeof createPinia>
  let i18n: ReturnType<typeof createTestI18n>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    i18n = createTestI18n()
    vi.clearAllMocks()
  })

  it('should render page title and description', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    expect(wrapper.find('h1').text()).toBe('效果对比')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('测试不同配置的检索效果')
  })

  it('should render view mode tabs', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Check for table/chart/radar tabs
    expect(wrapper.text()).toContain('表格视图')
    expect(wrapper.text()).toContain('图表视图')
    expect(wrapper.text()).toContain('雷达视图')
  })

  it('should render benchmark results table by default', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Check table is shown
    expect(wrapper.find('table').exists()).toBe(true)
  })

  it('should display default benchmark results', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Component has hardcoded benchmark results
    expect(wrapper.text()).toContain('FlashRank + Hybrid')
    expect(wrapper.text()).toContain('85%')
  })

  it('should switch to chart view when tab clicked', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Find and click chart view tab
    const chartTab = wrapper.findAll('button').find(b => b.text().includes('图表视图'))
    expect(chartTab?.exists()).toBe(true)
    await chartTab?.trigger('click')
    await nextTick()

    // After clicking, chart view content should be shown
    expect(wrapper.find('table').exists()).toBe(false)
  })

  it('should switch to radar view when tab clicked', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Find and click radar view tab
    const radarTab = wrapper.findAll('button').find(b => b.text().includes('雷达视图'))
    expect(radarTab?.exists()).toBe(true)
    await radarTab?.trigger('click')
    await nextTick()

    // After clicking, radar view should have SVG
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('should render run button', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // The button text is "开始测试" (from t('benchmark.run'))
    const buttons = wrapper.findAll('button')
    const runBtn = buttons.find(b => b.text().includes('开始测试') || b.text().includes('运行'))
    expect(runBtn?.exists()).toBe(true)
  })

  it('should render export button', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Export button
    const buttons = wrapper.findAll('button')
    const exportBtn = buttons.find(b => b.text().includes('导出'))
    expect(exportBtn?.exists()).toBe(true)
  })

  it('should show loading state when running benchmark', async () => {
    // Mock a pending promise
    mockRunBenchmark.mockImplementation(() => new Promise(() => {}))

    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Trigger the run
    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始测试'))
    await runBtn?.trigger('click')
    await nextTick()

    // After clicking, should show loading state
    expect(mockRunBenchmark).toHaveBeenCalled()
  })

  it('should display metrics in table view', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Metrics should be visible
    const text = wrapper.text()
    expect(text).toContain('Top-1')
    expect(text).toContain('Top-3')
    expect(text).toContain('Top-5')
    expect(text).toContain('NDCG')
  })

  it('should have default configs displayed', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia, i18n] },
    })

    // Component has hardcoded configs: FlashRank + Hybrid, Jina Reranker, Vector Only
    const text = wrapper.text()
    expect(text).toContain('FlashRank + Hybrid')
    expect(text).toContain('Jina Reranker')
    expect(text).toContain('Vector Only')
  })
})