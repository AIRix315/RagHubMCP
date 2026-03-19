import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConfigStore } from '@/stores/config'
import * as api from '@/api'

// Mock API
vi.mock('@/api', () => ({
  getConfig: vi.fn(),
  updateConfig: vi.fn(),
}))

describe('ConfigStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should initialize with null config', () => {
    const store = useConfigStore()
    expect(store.config).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should load config successfully', async () => {
    const mockConfig = {
      server: { host: 'localhost', port: 8000, debug: true },
      chroma: { persist_dir: './data', host: null, port: null },
      providers: {
        embedding: { default: 'ollama', instances: [] },
        rerank: { default: 'flashrank', instances: [] },
        llm: { default: '', instances: [] },
      },
      indexer: {
        chunk_size: 500,
        chunk_overlap: 50,
        max_file_size: 1048576,
        file_types: ['.py', '.ts'],
        exclude_dirs: ['node_modules'],
      },
      logging: { level: 'INFO', format: '%(message)s', file: null },
    }

    vi.mocked(api.getConfig).mockResolvedValue(mockConfig)

    const store = useConfigStore()
    await store.loadConfig()

    expect(store.config).toEqual(mockConfig)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should handle load error', async () => {
    vi.mocked(api.getConfig).mockRejectedValue(new Error('Network error'))

    const store = useConfigStore()
    await store.loadConfig()

    expect(store.config).toBeNull()
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })
})