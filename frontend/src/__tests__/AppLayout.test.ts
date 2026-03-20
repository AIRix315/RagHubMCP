import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AppLayout from '@/components/layout/AppLayout.vue'

// Mock lucide-vue-next icons
vi.mock('lucide-vue-next', () => ({
  Home: { name: 'Home', template: '<svg class="icon-home" />' },
  Settings: { name: 'Settings', template: '<svg class="icon-settings" />' },
  Database: { name: 'Database', template: '<svg class="icon-database" />' },
  BarChart3: { name: 'BarChart3', template: '<svg class="icon-chart" />' },
  SlidersHorizontal: { name: 'SlidersHorizontal', template: '<svg class="icon-sliders" />' },
}))

describe('AppLayout.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  const createTestRouter = () => {
    return createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div class="home">Home</div>' } },
        { path: '/config', name: 'config', component: { template: '<div>Config</div>' } },
        { path: '/collections', name: 'collections', component: { template: '<div>Collections</div>' } },
        { path: '/benchmark', name: 'benchmark', component: { template: '<div>Benchmark</div>' } },
        { path: '/settings', name: 'settings', component: { template: '<div>Settings</div>' } },
      ],
    })
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should render sidebar with title', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            template: '<a><slot /></a>',
            props: ['to'],
          },
        },
      },
      slots: {
        default: '<div class="slot-content">Content</div>',
      },
    })

    expect(wrapper.find('h1').text()).toBe('RagHubMCP')
    expect(wrapper.find('aside').exists()).toBe(true)
  })

  it('should render all navigation links', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            template: '<a class="nav-link"><slot /></a>',
            props: ['to', 'activeClass'],
          },
        },
      },
      slots: {
        default: '<div class="slot-content">Content</div>',
      },
    })

    const navLinks = wrapper.findAll('.nav-link')
    expect(navLinks.length).toBe(5)

    // Check navigation text content
    const navText = wrapper.find('nav').text()
    expect(navText).toContain('首页')
    expect(navText).toContain('配置管理')
    expect(navText).toContain('Collections')
    expect(navText).toContain('效果对比')
    expect(navText).toContain('系统设置')
  })

  it('should render slot content in main area', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            template: '<a><slot /></a>',
            props: ['to'],
          },
        },
      },
      slots: {
        default: '<div class="slot-content">Test Content</div>',
      },
    })

    expect(wrapper.find('.slot-content').text()).toBe('Test Content')
    expect(wrapper.find('main').exists()).toBe(true)
  })

  it('should have correct RouterLink active-class for home', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
      },
      slots: {
        default: '<div>Content</div>',
      },
    })

    const homeLink = wrapper.findAllComponents({ name: 'RouterLink' })[0]
    expect(homeLink.props('to')).toBe('/')
    expect(homeLink.props('activeClass')).toBe('bg-muted text-foreground')
  })

  it('should have correct RouterLink paths for all routes', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
      },
      slots: {
        default: '<div>Content</div>',
      },
    })

    const links = wrapper.findAllComponents({ name: 'RouterLink' })
    const paths = links.map(link => link.props('to'))

    expect(paths).toContain('/')
    expect(paths).toContain('/config')
    expect(paths).toContain('/collections')
    expect(paths).toContain('/benchmark')
    expect(paths).toContain('/settings')
  })

  it('should render icons for each navigation item', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            template: '<a><slot /></a>',
            props: ['to'],
          },
        },
      },
      slots: {
        default: '<div>Content</div>',
      },
    })

    // Check for mocked icons
    expect(wrapper.find('.icon-home').exists()).toBe(true)
    expect(wrapper.find('.icon-settings').exists()).toBe(true)
    expect(wrapper.find('.icon-database').exists()).toBe(true)
    expect(wrapper.find('.icon-chart').exists()).toBe(true)
    expect(wrapper.find('.icon-sliders').exists()).toBe(true)
  })

  it('should have correct layout structure', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia],
        stubs: {
          RouterLink: {
            name: 'RouterLink',
            template: '<a><slot /></a>',
            props: ['to'],
          },
        },
      },
      slots: {
        default: '<div>Content</div>',
      },
    })

    // Check layout structure
    expect(wrapper.find('.flex.min-h-screen').exists()).toBe(true)
    expect(wrapper.find('aside.w-64').exists()).toBe(true)
    expect(wrapper.find('main.flex-1').exists()).toBe(true)
  })
})