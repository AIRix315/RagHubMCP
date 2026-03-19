import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCollectionStore } from '@/stores/collection'
import * as api from '@/api'

// Mock API
vi.mock('@/api', () => ({
  listCollections: vi.fn(),
  deleteCollection: vi.fn(),
}))

describe('CollectionStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should initialize with empty collections', () => {
    const store = useCollectionStore()
    expect(store.collections).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should load collections successfully', async () => {
    const mockResponse = {
      collections: [
        { name: 'test-collection', count: 100, metadata: { created_at: Date.now() } },
      ],
      total: 1,
    }

    vi.mocked(api.listCollections).mockResolvedValue(mockResponse)

    const store = useCollectionStore()
    await store.loadCollections()

    expect(store.collections).toHaveLength(1)
    expect(store.collections[0].name).toBe('test-collection')
    expect(store.loading).toBe(false)
  })

  it('should handle delete collection', async () => {
    vi.mocked(api.listCollections).mockResolvedValue({ collections: [], total: 0 })
    vi.mocked(api.deleteCollection).mockResolvedValue({ name: 'test', message: 'deleted' })

    const store = useCollectionStore()
    await store.removeCollection('test')

    expect(api.deleteCollection).toHaveBeenCalledWith('test')
  })
})