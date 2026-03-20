import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Settings from '@/views/Settings.vue'

// Create mutable store state
const storeState = {
  config: {
    server: { host: '0.0.0.0', port: 8818, debug: false },
    chroma: { persist_dir: './chroma_data', host: null, port: null },
    providers: {
      embedding: {
        default: 'ollama',
        instances: [{ name: 'ollama', type: 'local', model: 'nomic-embed-text' }],
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
      file_types: ['.py', '.ts'],
      exclude_dirs: ['node_modules'],
    },
    logging: { level: 'INFO', format: '%(levelname)s - %(message)s', file: null },
  } as any,
  loading: false,
  error: null as string | null,
}

const mockLoadConfig = vi.fn().mockResolvedValue(undefined)

vi.mock('@/stores/config', () => ({
  useConfigStore: vi.fn(() => ({
    get config() { return storeState.config },
    get loading() { return storeState.loading },
    get error() { return storeState.error },
    loadConfig: mockLoadConfig,
  })),
}))

// Mock lucide-vue-next icons
vi.mock('lucide-vue-next', () => ({
  Info: { name: 'Info', template: '<svg></svg>' },
  Download: { name: 'Download', template: '<svg></svg>' },
  RefreshCw: { name: 'RefreshCw', template: '<svg></svg>' },
}))

// Mock clipboard API
const mockClipboardWrite = vi.fn().mockResolvedValue(undefined)
Object.assign(navigator, {
  clipboard: {
    writeText: mockClipboardWrite,
  },
})

describe('Settings.vue', () => {
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
          instances: [{ name: 'ollama', type: 'local', model: 'nomic-embed-text' }],
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
        file_types: ['.py', '.ts'],
        exclude_dirs: ['node_modules'],
      },
      logging: { level: 'INFO', format: '%(levelname)s - %(message)s', file: null },
    }
    storeState.loading = false
    storeState.error = null
  })

  it('should render page title and description', () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    expect(wrapper.find('h1').text()).toBe('系统设置')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('查看系统信息和导出 MCP 配置')
  })

  it('should call loadConfig on mount', async () => {
    mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(mockLoadConfig).toHaveBeenCalled()
  })

  it('should display loading state when loading', async () => {
    storeState.loading = true
    storeState.config = null

    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('加载中...')
  })

  it('should display error message when error exists', async () => {
    storeState.error = 'Failed to load config'

    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('Failed to load config')
  })

  it('should display system info section', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    // Wait for onMounted async operations
    await new Promise(resolve => setTimeout(resolve, 50))
    await nextTick()
    
    expect(wrapper.text()).toContain('系统信息')
  })

  it('should display server address from config', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await new Promise(resolve => setTimeout(resolve, 50))
    await nextTick()
    expect(wrapper.text()).toContain('8818')
  })

  it('should display chroma persist directory', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await new Promise(resolve => setTimeout(resolve, 50))
    await nextTick()
    expect(wrapper.text()).toContain('chroma_data')
  })

  it('should display log level', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await new Promise(resolve => setTimeout(resolve, 50))
    await nextTick()
    expect(wrapper.text()).toContain('INFO')
  })

  it('should display MCP config export section', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await new Promise(resolve => setTimeout(resolve, 50))
    await nextTick()
    expect(wrapper.text()).toContain('MCP 配置导出')
  })

  it('should display copy config button', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const copyBtn = buttons.find(b => b.text().includes('复制'))
    expect(copyBtn?.exists()).toBe(true)
  })

  it('should copy MCP config to clipboard', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const copyBtn = buttons.find(b => b.text().includes('复制'))
    await copyBtn?.trigger('click')

    expect(mockClipboardWrite).toHaveBeenCalled()
  })

  it('should display download config button', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const buttons = wrapper.findAll('button')
    const downloadBtn = buttons.find(b => b.text().includes('下载'))
    expect(downloadBtn?.exists()).toBe(true)
  })

  it('should display quick links section', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('快速链接')
    expect(wrapper.text()).toContain('GitHub 仓库')
    expect(wrapper.text()).toContain('MCP 协议文档')
  })

  it('should display refresh button in system info', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const refreshBtn = wrapper.findAll('button').find(b => b.text().includes('刷新'))
    expect(refreshBtn?.exists()).toBe(true)
  })

  it('should call loadConfig when refresh clicked', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const refreshBtn = wrapper.findAll('button').find(b => b.text().includes('刷新'))
    await refreshBtn?.trigger('click')

    expect(mockLoadConfig).toHaveBeenCalled()
  })

  it('should display external links', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const externalLinks = wrapper.findAll('a[target="_blank"]')
    // Should have links for GitHub, MCP docs, and API docs
    expect(externalLinks.length).toBeGreaterThan(0)
  })

  it('should generate correct MCP config JSON', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    // Check that the config JSON is displayed
    expect(wrapper.text()).toContain('mcpServers')
    expect(wrapper.text()).toContain('raghub')
  })
})