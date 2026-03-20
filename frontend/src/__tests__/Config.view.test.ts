import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Config from '@/views/Config.vue'

// Create mutable store state
const storeState = {
  config: {
    server: { host: '0.0.0.0', port: 8818, debug: false },
    chroma: { persist_dir: './chroma_data', host: null, port: null },
    providers: {
      embedding: {
        default: 'ollama',
        instances: [
          { name: 'ollama', type: 'local', model: 'nomic-embed-text', dimension: 768 },
          { name: 'openai', type: 'cloud', model: 'text-embedding-3-small', dimension: 1536 },
        ],
      },
      rerank: {
        default: 'flashrank',
        instances: [{ name: 'flashrank', type: 'local', model: 'default' }],
      },
      llm: {
        default: 'ollama',
        instances: [{ name: 'ollama', type: 'local', model: 'llama2' }],
      },
    },
    indexer: {
      chunk_size: 500,
      chunk_overlap: 50,
      max_file_size: 1048576,
      file_types: ['.py', '.ts', '.js', '.md'],
      exclude_dirs: ['node_modules', '.git', 'venv'],
    },
    logging: { level: 'INFO', format: '%(levelname)s - %(message)s', file: null },
  } as any,
  loading: false,
  error: null as string | null,
}

const mockLoadConfig = vi.fn().mockResolvedValue(undefined)
const mockSaveConfigData = vi.fn().mockResolvedValue(undefined)

vi.mock('@/stores/config', () => ({
  useConfigStore: vi.fn(() => ({
    get config() { return storeState.config },
    get loading() { return storeState.loading },
    get error() { return storeState.error },
    loadConfig: mockLoadConfig,
    saveConfigData: mockSaveConfigData,
  })),
}))

describe('Config.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    
    // Reset store state
    storeState.config = {
      server: { host: '0.0.0.0', port: 8818, debug: false },
      chroma: { persist_dir: './chroma_data', host: null, port: null },
      providers: {
        embedding: {
          default: 'ollama',
          instances: [
            { name: 'ollama', type: 'local', model: 'nomic-embed-text', dimension: 768 },
            { name: 'openai', type: 'cloud', model: 'text-embedding-3-small', dimension: 1536 },
          ],
        },
        rerank: {
          default: 'flashrank',
          instances: [{ name: 'flashrank', type: 'local', model: 'default' }],
        },
        llm: {
          default: 'ollama',
          instances: [{ name: 'ollama', type: 'local', model: 'llama2' }],
        },
      },
      indexer: {
        chunk_size: 500,
        chunk_overlap: 50,
        max_file_size: 1048576,
        file_types: ['.py', '.ts', '.js', '.md'],
        exclude_dirs: ['node_modules', '.git', 'venv'],
      },
      logging: { level: 'INFO', format: '%(levelname)s - %(message)s', file: null },
    }
    storeState.loading = false
    storeState.error = null
  })

  it('should render page title and description', () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    expect(wrapper.find('h1').text()).toBe('配置管理')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('管理系统配置和 Provider 设置')
  })

  it('should call loadConfig on mount', async () => {
    mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(mockLoadConfig).toHaveBeenCalled()
  })

  it('should display loading state when loading', async () => {
    storeState.loading = true
    storeState.config = null

    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('加载中...')
  })

  it('should display error message when error exists', async () => {
    storeState.error = 'Failed to load config'

    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('Failed to load config')
  })

  it('should display embedding providers table', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('Embedding Provider')
    expect(wrapper.text()).toContain('ollama')
    expect(wrapper.text()).toContain('nomic-embed-text')
  })

  it('should display rerank providers table', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('Rerank Provider')
    expect(wrapper.text()).toContain('flashrank')
  })

  it('should display indexer settings', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('索引设置')
    expect(wrapper.text()).toContain('Chunk Size')
    expect(wrapper.text()).toContain('Chunk Overlap')
  })

  it('should display supported file types', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('支持的文件类型')
    expect(wrapper.text()).toContain('.py')
    expect(wrapper.text()).toContain('.ts')
  })

  it('should display exclude directories', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('排除目录')
    expect(wrapper.text()).toContain('node_modules')
  })

  it('should display save button', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const saveBtn = buttons.find(b => b.text().includes('保存'))
    expect(saveBtn?.exists()).toBe(true)
  })

  it('should call saveConfigData when save button clicked', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const saveBtn = buttons.find(b => b.text().includes('保存'))
    await saveBtn?.trigger('click')

    expect(mockSaveConfigData).toHaveBeenCalled()
  })

  it('should render number inputs for indexer settings', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const inputs = wrapper.findAll('input[type="number"]')
    expect(inputs.length).toBeGreaterThan(0)
  })

  it('should show default embedding provider label', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('当前默认: ollama')
  })

  it('should display provider dimension if available', async () => {
    const wrapper = mount(Config, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('768')
  })
})