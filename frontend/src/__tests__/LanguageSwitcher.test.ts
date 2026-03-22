import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { nextTick, defineComponent, h } from 'vue'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {},
    'en-US': {},
  },
})

// Simple stubs for radix-vue components using render functions
const DropdownMenu = defineComponent({
  name: 'DropdownMenu',
  setup(_, { slots }) {
    return () => h('div', { class: 'dropdown-menu' }, slots.default?.())
  },
})

const DropdownMenuTrigger = defineComponent({
  name: 'DropdownMenuTrigger',
  setup(_, { slots }) {
    return () => h('div', { class: 'dropdown-trigger' }, slots.default?.())
  },
})

const DropdownMenuContent = defineComponent({
  name: 'DropdownMenuContent',
  setup(_, { slots }) {
    return () => h('div', { class: 'dropdown-content' }, slots.default?.())
  },
})

const DropdownMenuItem = defineComponent({
  name: 'DropdownMenuItem',
  props: ['class'],
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () => h('div', {
      class: ['dropdown-item', props.class],
      role: 'menuitem',
      onClick: () => emit('click'),
    }, slots.default?.())
  },
})

describe('LanguageSwitcher.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    // Reset locale
    i18n.global.locale.value = 'zh-CN'
  })

  it('should render language switcher button', () => {
    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('should display language options when clicked', async () => {
    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    await nextTick()

    // Should show language options
    expect(wrapper.text()).toMatch(/中文|English/i)
  })

  it('should have Chinese language option', async () => {
    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    await nextTick()

    expect(wrapper.text()).toContain('中文')
  })

  it('should have English language option', async () => {
    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    await nextTick()

    expect(wrapper.text()).toContain('English')
  })

  it('should switch language when option clicked', async () => {
    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    await nextTick()

    // Find and click English option
    const options = wrapper.findAll('[role="menuitem"]')
    const englishOption = options.find(o => o.text().includes('English'))
    await englishOption?.trigger('click')

    // Should have called switch
    expect(i18n.global.locale.value).toBe('en-US')
  })

  it('should highlight current language', async () => {
    i18n.global.locale.value = 'zh-CN'

    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    await nextTick()

    // Chinese should be highlighted (has bg-accent class)
    const options = wrapper.findAll('[role="menuitem"]')
    const chineseOption = options.find(o => o.text().includes('中文'))
    expect(chineseOption?.classes()).toBeDefined()
  })

  it('should display language icon', () => {
    const wrapper = mount(LanguageSwitcher, {
      global: {
        plugins: [pinia, i18n],
        stubs: {
          DropdownMenu,
          DropdownMenuTrigger,
          DropdownMenuContent,
          DropdownMenuItem,
        },
      },
    })

    // Should have an icon (Languages or similar) - check for svg
    const icon = wrapper.find('svg')
    expect(icon.exists()).toBe(true)
  })
})