import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Home from '@/views/Home.vue'

// Mock stores
vi.mock('@/stores/config', () => ({
  useConfigStore: vi.fn(() => ({
    config: {
      providers: {
        embedding: { default: 'ollama', instances: [{ name: 'ollama', type: 'local', model: 'nomic-embed-text' }] },
        rerank: { default: 'flashrank', instances: [{ name: 'flashrank', type: 'local', model: 'default' }] },
        llm: { default: 'ollama', instances: [{ name: 'ollama', type: 'local', model: 'llama2' }] },
      },
      indexer: { chunk_size: 500, chunk_overlap: 50, max_file_size: 1048576, file_types: ['.py', '.ts'] },
    },
    loadConfig: vi.fn().mockResolvedValue(undefined),
    loading: false,
    error: null,
  })),
}))

vi.mock('@/stores/collection', () => ({
  useCollectionStore: vi.fn(() => ({
    collections: [],
    totalCollections: 0,
    totalDocuments: 0,
    averageDocumentsPerCollection: 0,
    lastUpdated: new Date('2024-01-01T12:00:00'),
    loadCollections: vi.fn().mockResolvedValue(undefined),
    loading: false,
    error: null,
  })),
}))

// Mock API
vi.mock('@/api', () => ({
  listCollections: vi.fn().mockResolvedValue({ collections: [], total: 0 }),
  listIndexTasks: vi.fn().mockResolvedValue([]),
}))

describe('Home.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('should render dashboard title', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/', component: Home }],
    })

    const wrapper = mount(Home, {
      global: {
        plugins: [router, pinia],
      },
    })

    expect(wrapper.find('h1').text()).toContain('RagHubMCP 控制台')
  })

  it('should display stats cards after loading', async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: Home },
        { path: '/config', component: Home },
        { path: '/collections', component: Home },
        { path: '/benchmark', component: Home },
      ],
    })

    const wrapper = mount(Home, {
      global: {
        plugins: [router, pinia],
      },
    })

    // Wait for all async operations to complete
    await new Promise(resolve => setTimeout(resolve, 100))
    await nextTick()
    
    // Check for StatsCard components (they should be rendered after loading)
    const statsCards = wrapper.findAllComponents({ name: 'StatsCard' })
    expect(statsCards.length).toBeGreaterThan(0)
    
    // Check for ProviderStatus component
    const providerStatus = wrapper.findComponent({ name: 'ProviderStatus' })
    expect(providerStatus.exists()).toBe(true)
  })
})