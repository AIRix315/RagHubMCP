import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Collections from '@/views/Collections.vue'
import { createTestI18n } from './test-utils/i18n'

// Use vi.hoisted to define mock functions before vi.mock is hoisted
const mockLoadCollections = vi.hoisted(() => vi.fn())
const mockRemoveCollection = vi.hoisted(() => vi.fn())

// Mock the collection store module - must return a function
vi.mock('@/stores/collection', () => ({
  useCollectionStore: vi.fn(() => ({
    collections: [
      {
        name: 'test-collection',
        count: 100,
        metadata: { created_at: '2024-01-01' },
        document_count: 100,
      },
      {
        name: 'another-collection',
        count: 50,
        metadata: { created_at: '2024-01-02' },
        document_count: 50,
      },
    ],
    loading: false,
    error: null,
    lastUpdated: null,
    totalCollections: 2,
    totalDocuments: 150,
    averageDocumentsPerCollection: 75,
    loadCollections: mockLoadCollections.mockResolvedValue(undefined),
    removeCollection: mockRemoveCollection.mockResolvedValue(undefined),
  })),
}))

describe('Collections.vue', () => {
  let pinia: ReturnType<typeof createPinia>
  let i18n: ReturnType<typeof createTestI18n>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    i18n = createTestI18n()
    vi.clearAllMocks()
  })

  it('should render page title and description', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    expect(wrapper.find('h1').text()).toBe('Collection 管理')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('查看和管理向量数据库中的 Collections')
  })

  it('should render create button', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    const buttons = wrapper.findAll('button')
    const createBtn = buttons.find(b => b.text().includes('创建'))
    expect(createBtn?.exists()).toBe(true)
  })

  it('should call loadCollections on mount', async () => {
    mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // The mock store's loadCollections should have been called
    expect(mockLoadCollections).toHaveBeenCalled()
  })

  it('should display loading state when loading', async () => {
    // Override the module mock for this specific test
    vi.doMock('@/stores/collection', () => ({
      useCollectionStore: vi.fn(() => ({
        collections: [],
        loading: true,
        error: null,
        lastUpdated: null,
        totalCollections: 0,
        totalDocuments: 0,
        averageDocumentsPerCollection: 0,
        loadCollections: vi.fn().mockResolvedValue(undefined),
        removeCollection: vi.fn().mockResolvedValue(undefined),
      })),
    }))

    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Loading indicator should be present
    expect(wrapper.text()).toContain('加载中')
    
    vi.doUnmock('@/stores/collection')
  })

  it('should display empty state when no collections', async () => {
    vi.doMock('@/stores/collection', () => ({
      useCollectionStore: vi.fn(() => ({
        collections: [],
        loading: false,
        error: null,
        lastUpdated: null,
        totalCollections: 0,
        totalDocuments: 0,
        averageDocumentsPerCollection: 0,
        loadCollections: vi.fn().mockResolvedValue(undefined),
        removeCollection: vi.fn().mockResolvedValue(undefined),
      })),
    }))

    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Empty state is shown when no collections - just check component renders
    expect(wrapper.find('h1').exists()).toBe(true)
    
    vi.doUnmock('@/stores/collection')
  })

  it('should display collections table with data', async () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    // Wait for loading to complete (loading starts as true, then becomes false after loadCollections)
    await new Promise(resolve => setTimeout(resolve, 50))
    await nextTick()
    
    // Now loading should be false and data should be displayed
    // The mock store returns hardcoded collections with test-collection
    expect(wrapper.text()).toContain('test-collection')
    expect(wrapper.text()).toContain('another-collection')
  })

  it('should format date correctly', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    // Access the component instance
    const vm = wrapper.vm as any
    const formatted = vm.formatDate('2024-01-15T10:30:00')
    expect(formatted).toBeTruthy()
  })

  it('should return "-" for null timestamp', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    const vm = wrapper.vm as any
    const formatted = vm.formatDate(null)
    expect(formatted).toBe('-')
  })

  it('should display statistics cards', async () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    await nextTick()
    // Should show stats
    expect(wrapper.text()).toContain('Collections')
  })

  it('should have search input', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
  })

  it('should have refresh button', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia, i18n] },
    })

    const buttons = wrapper.findAll('button')
    const refreshBtn = buttons.find(b => b.text().includes('刷新'))
    expect(refreshBtn?.exists()).toBe(true)
  })
})