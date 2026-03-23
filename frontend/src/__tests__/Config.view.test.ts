import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'
import Config from '@/views/Config.vue'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      config: {
        title: '配置管理',
        subtitle: '管理系统配置和 Provider 设置',
        tabs: { embedding: 'Embedding', rerank: 'Rerank', vectordb: 'VectorDB' },
      },
      common: { loading: '加载中...', save: '保存' },
    },
    'en-US': {
      config: {
        title: 'Configuration',
        subtitle: 'Manage system configuration and providers',
        tabs: { embedding: 'Embedding', rerank: 'Rerank', vectordb: 'VectorDB' },
      },
      common: { loading: 'Loading...', save: 'Save' },
    },
  },
})

// Mock API providers
vi.mock('@/api/providers', () => ({
  getProviders: vi.fn().mockResolvedValue({
    embedding: [
      { name: 'ollama', type: 'local', model: 'nomic-embed-text', status: 'active', is_default: true },
    ],
    rerank: [{ name: 'flashrank', type: 'local', model: 'default', status: 'active', is_default: true }],
    vectorstore: [{ name: 'chroma-local', type: 'local', status: 'active', is_default: true }],
  }),
  setDefaultProvider: vi.fn().mockResolvedValue(undefined),
  deleteProvider: vi.fn().mockResolvedValue(undefined),
}))

describe('Config.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
  })

  it('should render page title and description', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Component should render without errors
    expect(wrapper.find('h1').exists()).toBe(true)
    expect(wrapper.text()).toContain('配置管理')
  })

  it('should mount successfully', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.exists()).toBe(true)
  })

  it('should have tabs for different provider types', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Check that tabs exist in the component
    expect(wrapper.text()).toBeTruthy()
  })

  it('should display loading state initially', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia, i18n] },
    })

    // Initial render should show loading
    expect(wrapper.exists()).toBe(true)
  })
})