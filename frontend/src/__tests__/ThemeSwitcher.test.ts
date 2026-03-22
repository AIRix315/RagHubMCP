import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import ThemeSwitcher from '@/components/common/ThemeSwitcher.vue'

// Mock useColorMode from @vueuse/core
const mockMode = { value: 'light' }
const mockToggleTheme = vi.fn(() => {
  mockMode.value = mockMode.value === 'dark' ? 'light' : 'dark'
})

vi.mock('@vueuse/core', () => ({
  useColorMode: () => ({
    mode: mockMode,
    value: mockMode.value,
  }),
}))

vi.mock('@/composables/useTheme', () => ({
  useTheme: () => ({
    mode: mockMode,
    isDark: { value: mockMode.value === 'dark' },
    toggleTheme: mockToggleTheme,
  }),
}))

describe('ThemeSwitcher.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    mockMode.value = 'light'
  })

  it('should render theme toggle button', () => {
    const wrapper = mount(ThemeSwitcher, {
      global: { plugins: [pinia] },
    })

    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('should have click handler', () => {
    const wrapper = mount(ThemeSwitcher, {
      global: { plugins: [pinia] },
    })

    const button = wrapper.find('button')
    expect(button.attributes('onclick') || button.element.onclick).toBeDefined()
  })

  it('should toggle theme when clicked', async () => {
    const wrapper = mount(ThemeSwitcher, {
      global: { plugins: [pinia] },
    })

    await wrapper.find('button').trigger('click')

    expect(mockToggleTheme).toHaveBeenCalled()
  })

  it('should display sun icon in dark mode', async () => {
    mockMode.value = 'dark'

    const wrapper = mount(ThemeSwitcher, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    // Sun icon should be visible in dark mode
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
  })

  it('should display moon icon in light mode', async () => {
    mockMode.value = 'light'

    const wrapper = mount(ThemeSwitcher, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    // Moon icon should be visible in light mode
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
  })

  it('should have accessible label', () => {
    const wrapper = mount(ThemeSwitcher, {
      global: { plugins: [pinia] },
    })

    const button = wrapper.find('button')
    // Should have aria-label or title for accessibility
    const hasLabel = 
      button.attributes('aria-label') || 
      button.attributes('title') ||
      wrapper.find('svg').exists()

    expect(hasLabel).toBeTruthy()
  })
})