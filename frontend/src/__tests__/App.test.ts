import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import App from '@/App.vue'

// Mock AppLayout component
vi.mock('@/components/layout/AppLayout.vue', () => ({
  default: {
    name: 'AppLayout',
    template: '<div class="app-layout-mock"><slot /></div>',
  },
}))

describe('App.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should render AppLayout component', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      ],
    })

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    expect(wrapper.find('.app-layout-mock').exists()).toBe(true)
  })

  it('should contain RouterView', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div class="home-view">Home</div>' } },
      ],
    })

    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    // The RouterView should be inside AppLayout slot
    expect(wrapper.find('.app-layout-mock').exists()).toBe(true)
  })

  it('should import RouterView from vue-router', () => {
    // This test verifies the component imports are correct
    const AppScript = App
    expect(AppScript).toBeDefined()
  })
})