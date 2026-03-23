import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AppLayout from '@/components/layout/AppLayout.vue'
import { createTestI18n } from './test-utils/i18n'

// Mock useTheme composable
vi.mock('@/composables/useTheme', () => ({
  useTheme: () => ({
    isDark: { value: false },
    toggleTheme: vi.fn(),
  }),
}))

// Mock useLocale composable
vi.mock('@/composables/useLocale', () => ({
  useLocale: () => ({
    locale: { value: 'zh-CN' },
    setLocale: vi.fn(),
  }),
}))

describe('AppLayout.vue', () => {
  let pinia: ReturnType<typeof createPinia>
  let i18n: ReturnType<typeof createTestI18n>

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
    i18n = createTestI18n()
  })

  it('should render sidebar with title', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia, i18n],
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

    // AppLayout uses a div with class "text-sm font-semibold" instead of h1
    expect(wrapper.find('.text-sm.font-semibold').text()).toBe('RagHubMCP')
    expect(wrapper.find('aside').exists()).toBe(true)
  })

  it('should render all navigation links', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia, i18n],
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
        plugins: [router, pinia, i18n],
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

  it('should have correct RouterLink paths for all routes', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, pinia, i18n],
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

  it('should render navigation items with correct paths', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, i18n],
      },
      slots: {
        default: '<div>Content</div>',
      },
    })

    // Check that navigation has 5 items (Home, Config, Collections, Benchmark, Settings)
    const nav = wrapper.find('nav')
    expect(nav.exists()).toBe(true)
    // Navigation items are rendered via v-for
    const navItems = nav.findAll('a')
    expect(navItems.length).toBe(5)
  })

  it('should have correct layout structure', async () => {
    const router = createTestRouter()

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [router, i18n],
      },
      slots: {
        default: '<div>Content</div>',
      },
    })

    // Check layout structure - actual uses w-60 not w-64
    expect(wrapper.find('.flex.min-h-screen').exists()).toBe(true)
    expect(wrapper.find('aside').exists()).toBe(true)
    expect(wrapper.find('main.flex-1').exists()).toBe(true)
  })
})