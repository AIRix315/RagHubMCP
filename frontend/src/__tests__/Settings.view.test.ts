import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Settings from '@/views/Settings.vue'
import { createTestI18n } from './test-utils/i18n'

// Mock demo-rerank module
vi.mock('@/demodata/demo-rerank', () => ({
  DEMO_RERANK_PROVIDERS: [],
  DEMO_RANK_TEST_DOCUMENTS: [],
  DEMO_RANK_SAMPLE_QUERIES: [],
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
  let i18n: ReturnType<typeof createTestI18n>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    i18n = createTestI18n()
    vi.clearAllMocks()
  })

  it('should render page title and description', () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    expect(wrapper.find('h1').text()).toBe('系统设置')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('查看系统信息和导出 MCP 配置')
  })

  it('should display system info section', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('系统信息')
  })

  it('should display server address from system info', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Component shows localhost:8818 in system info
    expect(wrapper.text()).toContain('8818')
  })

  it('should display storage directory', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Component shows ./data/chroma
    expect(wrapper.text()).toContain('./data/chroma')
  })

  it('should display log level', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Component shows INFO log level
    expect(wrapper.text()).toContain('INFO')
  })

  it('should switch to MCP tab when clicked', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    
    // Initially on System tab, so MCP config not visible
    expect(wrapper.text()).not.toContain('mcpServers')

    // Click MCP tab
    const tabs = wrapper.findAll('button')
    const mcpTab = tabs.find(b => b.text().includes('MCP 配置'))
    await mcpTab?.trigger('click')
    await nextTick()

    // Now MCP config should be visible
    expect(wrapper.text()).toContain('mcpServers')
    expect(wrapper.text()).toContain('raghub')
  })

  it('should display copy config button in MCP tab', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()

    // Click MCP tab to see the config
    const tabs = wrapper.findAll('button')
    const mcpTab = tabs.find(b => b.text().includes('MCP 配置'))
    await mcpTab?.trigger('click')
    await nextTick()

    const buttons = wrapper.findAll('button')
    const copyBtn = buttons.find(b => b.text().includes('复制'))
    expect(copyBtn?.exists()).toBe(true)
  })

  it('should copy MCP config to clipboard', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()

    // Click MCP tab first
    const tabs = wrapper.findAll('button')
    const mcpTab = tabs.find(b => b.text().includes('MCP 配置'))
    await mcpTab?.trigger('click')
    await nextTick()

    const buttons = wrapper.findAll('button')
    const copyBtn = buttons.find(b => b.text().includes('复制'))
    await copyBtn?.trigger('click')

    expect(mockClipboardWrite).toHaveBeenCalled()
  })

  it('should display download config button in MCP tab', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()

    // Click MCP tab first
    const tabs = wrapper.findAll('button')
    const mcpTab = tabs.find(b => b.text().includes('MCP 配置'))
    await mcpTab?.trigger('click')
    await nextTick()

    const buttons = wrapper.findAll('button')
    const downloadBtn = buttons.find(b => b.text().includes('下载'))
    expect(downloadBtn?.exists()).toBe(true)
  })

  it('should display tabs for System, MCP, Logs, DevTools', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    
    // Check for all tab labels
    expect(wrapper.text()).toContain('系统信息')
    expect(wrapper.text()).toContain('MCP 配置')
    expect(wrapper.text()).toContain('系统日志')
    expect(wrapper.text()).toContain('开发工具')
  })

  it('should generate correct MCP config JSON in MCP tab', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()

    // Click MCP tab first
    const tabs = wrapper.findAll('button')
    const mcpTab = tabs.find(b => b.text().includes('MCP 配置'))
    await mcpTab?.trigger('click')
    await nextTick()

    // Check that the config JSON is displayed
    expect(wrapper.text()).toContain('mcpServers')
    expect(wrapper.text()).toContain('raghub')
  })

  it('should display version info', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('2.5.2')
  })

  it('should switch to Logs tab when clicked', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()

    // Click Logs tab
    const tabs = wrapper.findAll('button')
    const logsTab = tabs.find(b => b.text().includes('系统日志'))
    await logsTab?.trigger('click')
    await nextTick()

    // Should show logs content
    expect(wrapper.text()).toContain('INFO')
    expect(wrapper.text()).toContain('WARN')
  })

  it('should switch to DevTools tab when clicked', async () => {
    const wrapper = mount(Settings, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()

    // Click DevTools tab
    const tabs = wrapper.findAll('button')
    const devtoolsTab = tabs.find(b => b.text().includes('开发工具'))
    await devtoolsTab?.trigger('click')
    await nextTick()

    // Should show DevTools content
    expect(wrapper.text()).toContain('示例数据')
  })
})