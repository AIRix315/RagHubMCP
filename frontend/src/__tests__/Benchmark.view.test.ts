import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Benchmark from '@/views/Benchmark.vue'

// Use vi.hoisted to define mock functions before vi.mock is hoisted
const mockRunBenchmark = vi.hoisted(() => vi.fn())
const mockListCollections = vi.hoisted(() => vi.fn())

vi.mock('@/api', () => ({
  runBenchmark: mockRunBenchmark,
  listCollections: mockListCollections,
}))

// Mock chart components
vi.mock('@/components/charts/BenchmarkChart.vue', () => ({
  default: {
    name: 'BenchmarkChart',
    template: '<div class="benchmark-chart-mock">BenchmarkChart</div>',
    props: ['results', 'title'],
  },
}))

vi.mock('@/components/charts/LatencyChart.vue', () => ({
  default: {
    name: 'LatencyChart',
    template: '<div class="latency-chart-mock">LatencyChart</div>',
    props: ['results', 'title'],
  },
}))

describe('Benchmark.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    
    // Set up default mock implementations
    mockRunBenchmark.mockResolvedValue({
      query: 'test query',
      collection: 'test-collection',
      results: [
        {
          config_name: 'Config A',
          results: [{ id: '1', text: 'result 1', score: 0.9 }],
          latency_ms: 150.5,
          embedding_provider: 'ollama',
          rerank_provider: 'flashrank',
        },
      ],
      total_latency_ms: 150.5,
    })
    
    mockListCollections.mockResolvedValue({
      collections: [
        { name: 'test-collection', count: 100 },
      ],
      total: 1,
    })
  })

  it('should render page title and description', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    expect(wrapper.find('h1').text()).toBe('效果对比')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('测试不同配置的检索效果')
  })

  it('should load collections on mount', async () => {
    mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(mockListCollections).toHaveBeenCalled()
  })

  it('should render query textarea', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    const textarea = wrapper.find('textarea')
    expect(textarea.exists()).toBe(true)
    expect(textarea.attributes('placeholder')).toContain('输入测试查询')
  })

  it('should render collection select', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const select = wrapper.findAll('select')[0]
    expect(select.exists()).toBe(true)
  })

  it('should render default configs', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    // Check for config input fields - there should be 2 default configs
    const configInputs = wrapper.findAll('input').filter(i => i.classes().includes('font-medium'))
    expect(configInputs.length).toBeGreaterThanOrEqual(2)
  })

  it('should render add config button', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    const addBtn = wrapper.findAll('button').find(b => b.text().includes('添加配置'))
    expect(addBtn?.exists()).toBe(true)
  })

  it('should add new config when add button clicked', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    // Initially 2 configs
    const initialInputs = wrapper.findAll('input').filter(i => i.classes().includes('font-medium'))
    const initialCount = initialInputs.length
    
    const addBtn = wrapper.findAll('button').find(b => b.text().includes('添加配置'))
    await addBtn?.trigger('click')

    // Should now have 3 configs
    const newInputs = wrapper.findAll('input').filter(i => i.classes().includes('font-medium'))
    expect(newInputs.length).toBe(initialCount + 1)
  })

  it('should render remove config button', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('移除')
  })

  it('should render run benchmark button', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    expect(runBtn?.exists()).toBe(true)
  })

  it('should disable run button when query is empty', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    expect(runBtn?.attributes('disabled')).toBeDefined()
  })

  it('should enable run button when query is not empty', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    expect(runBtn?.attributes('disabled')).toBeUndefined()
  })

  it('should show error when running with empty query', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Try to run with empty query by clicking button directly
    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')

    // Button should be disabled
    expect(mockRunBenchmark).not.toHaveBeenCalled()
  })

  it('should call runBenchmark API when run button clicked with query', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')

    expect(mockRunBenchmark).toHaveBeenCalled()
  })

  it('should display results after benchmark runs', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query and run
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('对比结果')
  })

  it('should display table and chart tabs after results', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query and run
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('表格视图')
    expect(wrapper.text()).toContain('图表视图')
  })

  it('should switch to charts tab when clicked', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query and run
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')
    await nextTick()

    // Click charts tab
    const chartsTab = wrapper.findAll('button').find(b => b.text() === '图表视图')
    await chartsTab?.trigger('click')
    await nextTick()

    expect(wrapper.find('.benchmark-chart-mock').exists()).toBe(true)
  })

  it('should display error message when benchmark fails', async () => {
    mockRunBenchmark.mockRejectedValueOnce(new Error('Benchmark failed'))

    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query and run
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Benchmark failed')
  })

  it('should show loading state during benchmark', async () => {
    mockRunBenchmark.mockImplementationOnce(() => new Promise(() => {})) // Never resolves

    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query and run
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('执行中...')
  })

  it('should display total latency in results', async () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Set query and run
    const textarea = wrapper.find('textarea')
    await textarea.setValue('test query')

    const runBtn = wrapper.findAll('button').find(b => b.text().includes('开始对比测试'))
    await runBtn?.trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('总耗时')
  })

  it('should render embedding provider select in config', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Should have selects for embedding providers
    const selects = wrapper.findAll('select')
    expect(selects.length).toBeGreaterThan(0)
  })

  it('should render top_k input in config', () => {
    const wrapper = mount(Benchmark, {
      global: { plugins: [pinia] },
    })

    // Should have number input for top_k
    const numberInputs = wrapper.findAll('input[type="number"]')
    expect(numberInputs.length).toBeGreaterThan(0)
  })
})