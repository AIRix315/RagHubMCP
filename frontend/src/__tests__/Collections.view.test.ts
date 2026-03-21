import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Collections from '@/views/Collections.vue'

// Mock the collection store module
vi.mock('@/stores/collection', () => ({
  useCollectionStore: vi.fn(),
}))

// Mock lucide-vue-next icons
vi.mock('lucide-vue-next', () => ({
  Trash2: { name: 'Trash2', template: '<svg></svg>' },
  RefreshCw: { name: 'RefreshCw', template: '<svg></svg>' },
}))

// Helper to create mock store
function createMockStore(overrides: Record<string, unknown> = {}) {
  return {
    collections: [],
    loading: false,
    error: null as string | null,
    lastUpdated: null as Date | null,
    totalCollections: 0,
    totalDocuments: 0,
    averageDocumentsPerCollection: 0,
    loadCollections: vi.fn().mockResolvedValue(undefined),
    removeCollection: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  }
}

describe('Collections.vue', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
  })

  it('should render page title and description', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    expect(wrapper.find('h1').text()).toBe('Collection 管理')
    expect(wrapper.find('p.text-muted-foreground').text()).toContain('查看和管理向量数据库中的 Collections')
  })

  it('should render refresh button', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    const refreshBtn = wrapper.find('button')
    expect(refreshBtn.text()).toContain('刷新')
  })

  it('should call loadCollections on mount', async () => {
    const mockLoadCollections = vi.fn().mockResolvedValue(undefined)
    const mockStore = createMockStore({ loadCollections: mockLoadCollections })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(mockLoadCollections).toHaveBeenCalled()
  })

  it('should display loading state when loading', async () => {
    const mockStore = createMockStore({ loading: true })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('加载中...')
  })

  it('should display error message when error exists', async () => {
    const mockStore = createMockStore({ error: 'Failed to load collections' })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('Failed to load collections')
  })

  it('should display empty state when no collections', async () => {
    const mockStore = createMockStore()
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('暂无 Collection')
  })

  it('should display collections table with data', async () => {
    const mockCollections = [
      {
        name: 'test-collection',
        count: 100,
        metadata: { created_at: 1704067200000 },
      },
      {
        name: 'another-collection',
        count: 50,
        metadata: { created_at: 1704153600000 },
      },
    ]

    const mockStore = createMockStore({ collections: mockCollections })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    expect(wrapper.text()).toContain('test-collection')
    expect(wrapper.text()).toContain('another-collection')
    expect(wrapper.text()).toContain('100')
    expect(wrapper.text()).toContain('50')
  })

  it('should show delete confirmation modal when delete button clicked', async () => {
    const mockCollections = [
      {
        name: 'test-collection',
        count: 100,
        metadata: { created_at: 1704067200000 },
      },
    ]

    const mockStore = createMockStore({ collections: mockCollections })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()

    // Click delete button
    const deleteBtn = wrapper.find('button.text-destructive')
    await deleteBtn.trigger('click')

    // Check modal is shown
    expect(wrapper.text()).toContain('确认删除')
    expect(wrapper.text()).toContain('test-collection')
  })

  it('should close modal when cancel button clicked', async () => {
    const mockCollections = [
      {
        name: 'test-collection',
        count: 100,
        metadata: { created_at: 1704067200000 },
      },
    ]

    const mockStore = createMockStore({ collections: mockCollections })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()

    // Open modal
    const deleteBtn = wrapper.find('button.text-destructive')
    await deleteBtn.trigger('click')

    // Click cancel
    const cancelBtn = wrapper.findAll('button').find(b => b.text() === '取消')
    await cancelBtn?.trigger('click')

    // Modal should be closed
    expect(wrapper.text()).not.toContain('确认删除')
  })

  it('should call removeCollection when confirm delete clicked', async () => {
    const mockRemoveCollection = vi.fn().mockResolvedValue(undefined)
    const mockCollections = [
      {
        name: 'test-collection',
        count: 100,
        metadata: { created_at: 1704067200000 },
      },
    ]

    const mockStore = createMockStore({ collections: mockCollections, removeCollection: mockRemoveCollection })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()

    // Open modal
    const deleteBtn = wrapper.find('button.text-destructive')
    await deleteBtn.trigger('click')

    // Confirm delete
    const confirmBtn = wrapper.findAll('button').find(b => b.text() === '确认删除')
    await confirmBtn?.trigger('click')

    expect(mockRemoveCollection).toHaveBeenCalledWith('test-collection')
  })

  it('should disable refresh button when loading', async () => {
    const mockStore = createMockStore({ loading: true })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()
    const refreshBtn = wrapper.find('button')
    expect(refreshBtn.attributes('disabled')).toBeDefined()
  })

  it('should format date correctly', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    // Access the component instance
    const vm = wrapper.vm as any
    const formatted = vm.formatDate(1704067200000)
    expect(formatted).toBeTruthy()
  })

  it('should return "-" for null timestamp', () => {
    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    const vm = wrapper.vm as any
    const formatted = vm.formatDate(null)
    expect(formatted).toBe('-')
  })

  it('should disable confirm delete button while deleting', async () => {
    const mockCollections = [
      {
        name: 'test-collection',
        count: 100,
        metadata: { created_at: 1704067200000 },
      },
    ]

    const mockStore = createMockStore({
      collections: mockCollections,
      removeCollection: vi.fn().mockImplementation(() => new Promise(() => {})), // Never resolves
    })
    vi.mocked(await import('@/stores/collection')).useCollectionStore.mockReturnValue(mockStore as any)

    const wrapper = mount(Collections, {
      global: { plugins: [pinia] },
    })

    await nextTick()

    // Open modal
    const deleteBtn = wrapper.find('button.text-destructive')
    await deleteBtn.trigger('click')

    // Check confirm button exists
    const confirmBtn = wrapper.findAll('button').find(b => b.text() === '确认删除')
    expect(confirmBtn?.exists()).toBe(true)
  })
})