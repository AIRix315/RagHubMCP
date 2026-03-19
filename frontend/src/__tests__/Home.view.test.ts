import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'

// Mock stores and API
vi.mock('@/stores/config', () => ({
  useConfigStore: () => ({
    config: {
      providers: {
        embedding: { default: 'ollama' },
        rerank: { default: 'flashrank' },
      },
      indexer: { chunk_size: 500 },
    },
    loadConfig: vi.fn(),
    loading: false,
    error: null,
  }),
}))

vi.mock('@/api', () => ({
  listCollections: vi.fn().mockResolvedValue({ collections: [], total: 0 }),
}))

describe('Home.vue', () => {
  it('should render dashboard title', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/', component: Home }],
    })

    const wrapper = mount(Home, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('h1').text()).toContain('RagHubMCP 控制台')
  })

  it('should display stats cards', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/', component: Home }],
    })

    const wrapper = mount(Home, {
      global: {
        plugins: [router],
      },
    })

    const statsCards = wrapper.findAll('.rounded-lg.border.bg-card')
    expect(statsCards.length).toBeGreaterThan(0)
  })
})