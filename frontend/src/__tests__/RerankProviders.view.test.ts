import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'
import RerankProviders from '@/views/Config/Providers/Rerank.vue'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      rerank: {
        providers: 'Rerank 提供者',
        description: '管理 Rerank 提供者配置',
        add_provider: '添加提供者',
        batch_size: '批处理大小',
        delete_confirm: '确定删除？',
      },
      common: {
        name: '名称',
        type: '类型',
        model: '模型',
        status: '状态',
        action: '操作',
        default: '默认',
        active: '启用',
        inactive: '禁用',
        test: '测试',
        edit: '编辑',
        loading: '加载中...',
      },
    },
    'en-US': {
      rerank: {
        providers: 'Rerank Providers',
        description: 'Manage Rerank provider configurations',
        add_provider: 'Add Provider',
        batch_size: 'Batch Size',
        delete_confirm: 'Are you sure to delete?',
      },
      common: {
        name: 'Name',
        type: 'Type',
        model: 'Model',
        status: 'Status',
        action: 'Action',
        default: 'Default',
        active: 'Active',
        inactive: 'Inactive',
        test: 'Test',
        edit: 'Edit',
        loading: 'Loading...',
      },
    },
  },
})

// Mock rerank store state
const storeState = {
  providers: [
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
  ],
  loading: false,
  error: null as string | null,
}

const mockLoadProviders = vi.fn().mockResolvedValue(undefined)
const mockTestProvider = vi.fn().mockResolvedValue({ latency_ms: 45, success: true })
const mockSetDefault = vi.fn().mockResolvedValue(undefined)
const mockDeleteProvider = vi.fn().mockResolvedValue(undefined)

vi.mock('@/stores/rerank', () => ({
  useRerankStore: vi.fn(() => ({
    get providers() { return storeState.providers },
    get loading() { return storeState.loading },
    get error() { return storeState.error },
    loadProviders: mockLoadProviders,
    testProvider: mockTestProvider,
    setDefault: mockSetDefault,
    deleteProvider: mockDeleteProvider,
  })),
}))

describe('RerankProviders.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    storeState.loading = false
    storeState.error = null
    // Reset providers to default state
    storeState.providers = [
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
  })

  it('should render page title', () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    expect(wrapper.find('h1').text()).toContain('Rerank')
  })

  it('should render add provider button', () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    const buttons = wrapper.findAll('button')
    const addBtn = buttons.find(b => b.text().includes('添加') || b.text().includes('Add'))
    expect(addBtn?.exists()).toBe(true)
  })

  it('should display provider list', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('onnx-tiny')
    expect(wrapper.text()).toContain('onnx-minilm')
  })

  it('should display provider status indicators', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Status should be shown (active/inactive)
    expect(wrapper.text()).toMatch(/启用|禁用|active|inactive/i)
  })

  it('should display model name for each provider', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('TinyBERT')
    expect(wrapper.text()).toContain('MiniLM')
  })

  it('should show default badge for default provider', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toMatch(/默认|default/i)
  })

  it('should have edit button for each provider', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const editButtons = buttons.filter(b => b.text().includes('编辑') || b.text().includes('Edit'))
    expect(editButtons.length).toBeGreaterThan(0)
  })

  it('should have test button for each provider', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const testButtons = buttons.filter(b => b.text().includes('测试') || b.text().includes('Test'))
    expect(testButtons.length).toBeGreaterThan(0)
  })

  it('should call testProvider when test button clicked', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const testBtn = buttons.find(b => b.text().includes('测试') || b.text().includes('Test'))
    await testBtn?.trigger('click')

    expect(mockTestProvider).toHaveBeenCalled()
  })

  it('should display loading state', async () => {
    storeState.loading = true
    storeState.providers = []

    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toMatch(/加载|loading/i)
  })

  it('should display error message when error exists', async () => {
    storeState.error = 'Failed to load providers'

    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('Failed to load providers')
  })

  it('should display engine type badge', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('ONNX')
  })

  it('should display batch_size config', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('32')
  })

  it('should call setDefault when set default button clicked', async () => {
    const wrapper = mount(RerankProviders, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Find the Star button by aria-label (默认/default)
    const defaultBtn = wrapper.find('button[aria-label="默认"]')
    await defaultBtn.trigger('click')

    expect(mockSetDefault).toHaveBeenCalled()
  })
})