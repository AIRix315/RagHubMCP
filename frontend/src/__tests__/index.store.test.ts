import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIndexStore } from '@/stores/index'
import * as api from '@/api'
import { getErrorMessage } from '@/api/errors'
import type { ProgressData } from '@/composables/useWebSocket'

// Mock API
vi.mock('@/api', () => ({
  startIndex: vi.fn(),
  getIndexStatus: vi.fn(),
}))

// Mock error handler
vi.mock('@/api/errors', () => ({
  getErrorMessage: vi.fn((e: unknown) => (e instanceof Error ? e.message : 'Unknown error')),
}))

// Track onUnmounted callbacks
const onUnmountedCallbacks: (() => void)[] = []

// Mock useWebSocket composable
const mockWebSocket = {
  isConnected: { value: false },
  progressData: { value: null as ProgressData | null },
  connect: vi.fn(),
  disconnect: vi.fn(),
  _callbacks: {
    onProgress: null as ((data: ProgressData) => void) | null,
    onConnected: null as (() => void) | null,
    onDisconnected: null as (() => void) | null,
    onError: null as ((errorMsg: string) => void) | null,
  },
}

vi.mock('@/composables/useWebSocket', () => ({
  useWebSocket: vi.fn((options) => {
    mockWebSocket._callbacks.onProgress = options.onProgress || null
    mockWebSocket._callbacks.onConnected = options.onConnected || null
    mockWebSocket._callbacks.onDisconnected = options.onDisconnected || null
    mockWebSocket._callbacks.onError = options.onError || null
    return mockWebSocket
  }),
}))

// Mock vue's onUnmounted
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onUnmounted: (callback: () => void) => {
      onUnmountedCallbacks.push(callback)
    },
  }
})

describe('IndexStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.useFakeTimers()
    onUnmountedCallbacks.length = 0
    // Reset mock WebSocket state
    mockWebSocket.isConnected.value = false
    mockWebSocket.progressData.value = null
    mockWebSocket._callbacks = {
      onProgress: null,
      onConnected: null,
      onDisconnected: null,
      onError: null,
    }
    // Reset mockWebSocket.connect to default (no-op)
    mockWebSocket.connect.mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('initialization', () => {
    it('should initialize with default state', () => {
      const store = useIndexStore()

      expect(store.currentTask).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.isConnected).toBe(false)
    })
  })

  describe('start action', () => {
    it('should start indexing successfully with WebSocket', async () => {
      const mockResponse = {
        task_id: 'task-123',
        message: 'Indexing started',
        status_url: '/api/index/status/task-123',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files', 'test-collection')

      expect(api.startIndex).toHaveBeenCalledWith({
        path: '/path/to/files',
        collection_name: 'test-collection',
      })
      expect(store.currentTask).not.toBeNull()
      expect(store.currentTask?.task_id).toBe('task-123')
      expect(store.currentTask?.status).toBe('pending')
      expect(store.loading).toBe(false)
      expect(mockWebSocket.connect).toHaveBeenCalledWith('task-123')
    })

    it('should start indexing with default collection name', async () => {
      const mockResponse = {
        task_id: 'task-456',
        message: 'Indexing started',
        status_url: '/api/index/status/task-456',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      expect(api.startIndex).toHaveBeenCalledWith({
        path: '/path/to/files',
        collection_name: 'default',
      })
    })

    it('should fall back to polling when WebSocket connection fails', async () => {
      const mockResponse = {
        task_id: 'task-789',
        message: 'Indexing started',
        status_url: '/api/index/status/task-789',
      }

      const mockStatus = {
        task_id: 'task-789',
        status: 'running' as const,
        progress: 50,
        message: 'Processing',
        total_files: 10,
        processed_files: 5,
        total_chunks: 100,
        created_at: new Date().toISOString(),
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)
      vi.mocked(api.getIndexStatus).mockResolvedValue(mockStatus)

      // Make WebSocket connect throw
      mockWebSocket.connect.mockImplementation(() => {
        throw new Error('WebSocket connection failed')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const store = useIndexStore()
      await store.start('/path/to/files')

      expect(consoleSpy).toHaveBeenCalledWith(
        'WebSocket connection failed, falling back to polling:',
        expect.any(Error)
      )
      expect(api.getIndexStatus).toHaveBeenCalledWith('task-789')

      consoleSpy.mockRestore()
    })

    it('should handle API error when starting index', async () => {
      const error = new Error('Path not found')
      vi.mocked(api.startIndex).mockRejectedValue(error)
      vi.mocked(getErrorMessage).mockReturnValue('Path not found')

      const store = useIndexStore()
      await store.start('/invalid/path')

      expect(store.error).toBe('Path not found')
      expect(store.loading).toBe(false)
      expect(store.currentTask).toBeNull()
    })

    it('should set loading state during start', async () => {
      let resolveStart: (value: unknown) => void
      vi.mocked(api.startIndex).mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveStart = resolve
          })
      )

      const store = useIndexStore()
      const startPromise = store.start('/path/to/files')

      // Check loading is true during the operation
      expect(store.loading).toBe(true)

      // Resolve the promise
      resolveStart!({
        task_id: 'task-001',
        message: 'Started',
        status_url: '/api/index/status/task-001',
      })
      await startPromise

      expect(store.loading).toBe(false)
    })
  })

  describe('handleProgressUpdate', () => {
    it('should update currentTask with progress data', async () => {
      const mockResponse = {
        task_id: 'task-progress',
        message: 'Indexing started',
        status_url: '/api/index/status/task-progress',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Simulate WebSocket progress update
      const progressData: ProgressData = {
        status: 'running',
        progress: 75,
        message: 'Processing files...',
        total_files: 20,
        processed_files: 15,
        total_chunks: 200,
      }

      // Call the onProgress callback that was registered
      mockWebSocket._callbacks.onProgress?.(progressData)

      expect(store.currentTask).not.toBeNull()
      expect(store.currentTask?.status).toBe('running')
      expect(store.currentTask?.progress).toBe(75)
      expect(store.currentTask?.message).toBe('Processing files...')
      expect(store.currentTask?.total_files).toBe(20)
      expect(store.currentTask?.processed_files).toBe(15)
      expect(store.currentTask?.total_chunks).toBe(200)
    })

    it('should disconnect WebSocket when task completes', async () => {
      const mockResponse = {
        task_id: 'task-complete',
        message: 'Indexing started',
        status_url: '/api/index/status/task-complete',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Simulate completion
      const progressData: ProgressData = {
        status: 'completed',
        progress: 100,
        message: 'Indexing completed',
        total_files: 10,
        processed_files: 10,
        total_chunks: 100,
      }

      mockWebSocket._callbacks.onProgress?.(progressData)

      expect(mockWebSocket.disconnect).toHaveBeenCalled()
    })

    it('should disconnect WebSocket when task fails', async () => {
      const mockResponse = {
        task_id: 'task-fail',
        message: 'Indexing started',
        status_url: '/api/index/status/task-fail',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Simulate failure
      const progressData: ProgressData = {
        status: 'failed',
        progress: 50,
        message: 'Indexing failed',
        total_files: 10,
        processed_files: 5,
        total_chunks: 50,
        error: 'File read error',
      }

      mockWebSocket._callbacks.onProgress?.(progressData)

      expect(mockWebSocket.disconnect).toHaveBeenCalled()
      expect(store.currentTask?.error).toBe('File read error')
    })
  })

  describe('WebSocket connection status', () => {
    it('should update isConnected when WebSocket connects', async () => {
      const mockResponse = {
        task_id: 'task-ws',
        message: 'Indexing started',
        status_url: '/api/index/status/task-ws',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Simulate WebSocket connected
      mockWebSocket._callbacks.onConnected?.()

      expect(store.isConnected).toBe(true)
    })

    it('should update isConnected when WebSocket disconnects', async () => {
      const mockResponse = {
        task_id: 'task-ws-disc',
        message: 'Indexing started',
        status_url: '/api/index/status/task-ws-disc',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Connect first
      mockWebSocket._callbacks.onConnected?.()
      expect(store.isConnected).toBe(true)

      // Then disconnect
      mockWebSocket._callbacks.onDisconnected?.()
      expect(store.isConnected).toBe(false)
    })

    it('should fall back to polling on WebSocket error', async () => {
      const mockResponse = {
        task_id: 'task-ws-err',
        message: 'Indexing started',
        status_url: '/api/index/status/task-ws-err',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Simulate WebSocket error
      mockWebSocket._callbacks.onError?.('WebSocket connection lost')

      expect(consoleSpy).toHaveBeenCalledWith('WebSocket error:', 'WebSocket connection lost')

      consoleSpy.mockRestore()
    })
  })

  describe('getStatus action', () => {
    it('should get task status successfully', async () => {
      const mockStatus = {
        task_id: 'task-status',
        status: 'running' as const,
        progress: 60,
        message: 'Processing...',
        total_files: 10,
        processed_files: 6,
        total_chunks: 100,
        created_at: new Date().toISOString(),
      }

      vi.mocked(api.getIndexStatus).mockResolvedValue(mockStatus)

      const store = useIndexStore()
      const status = await store.getStatus('task-status')

      expect(api.getIndexStatus).toHaveBeenCalledWith('task-status')
      expect(status).toEqual(mockStatus)
      expect(store.currentTask).toEqual(mockStatus)
    })

    it('should handle getStatus error', async () => {
      const error = new Error('Task not found')
      vi.mocked(api.getIndexStatus).mockRejectedValue(error)
      vi.mocked(getErrorMessage).mockReturnValue('Task not found')

      const store = useIndexStore()

      await expect(store.getStatus('invalid-task')).rejects.toThrow()
      expect(store.error).toBe('Task not found')
    })
  })

  describe('stopMonitoring action', () => {
    it('should stop monitoring and clear state', async () => {
      const mockResponse = {
        task_id: 'task-stop',
        message: 'Indexing started',
        status_url: '/api/index/status/task-stop',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      expect(store.currentTask).not.toBeNull()

      store.stopMonitoring()

      expect(mockWebSocket.disconnect).toHaveBeenCalled()
      expect(store.currentTask).toBeNull()
    })

    it('should stop polling when monitoring stops', async () => {
      const mockResponse = {
        task_id: 'task-poll-stop',
        message: 'Indexing started',
        status_url: '/api/index/status/task-poll-stop',
      }

      const mockStatus = {
        task_id: 'task-poll-stop',
        status: 'running' as const,
        progress: 30,
        message: 'Processing',
        total_files: 10,
        processed_files: 3,
        total_chunks: 50,
        created_at: new Date().toISOString(),
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)
      vi.mocked(api.getIndexStatus).mockResolvedValue(mockStatus)

      // Force polling by making WebSocket fail
      mockWebSocket.connect.mockImplementation(() => {
        throw new Error('WS failed')
      })

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Start polling
      vi.advanceTimersByTime(1000)
      expect(api.getIndexStatus).toHaveBeenCalled()

      // Stop monitoring
      store.stopMonitoring()

      // Clear the mock to check if more calls happen
      vi.mocked(api.getIndexStatus).mockClear()

      // Advance time - should not call getStatus anymore
      vi.advanceTimersByTime(2000)
      expect(api.getIndexStatus).not.toHaveBeenCalled()
    })
  })

  describe('clearCurrentTask action', () => {
    it('should clear current task and error', async () => {
      const mockResponse = {
        task_id: 'task-clear',
        message: 'Indexing started',
        status_url: '/api/index/status/task-clear',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Set an error
      store.error = 'Some error'

      store.clearCurrentTask()

      expect(store.currentTask).toBeNull()
      expect(store.error).toBeNull()
      expect(mockWebSocket.disconnect).toHaveBeenCalled()
    })
  })

  describe('polling (pollStatus)', () => {
    it('should poll for status updates', async () => {
      const mockResponse = {
        task_id: 'task-poll',
        message: 'Indexing started',
        status_url: '/api/index/status/task-poll',
      }

      const mockStatus1 = {
        task_id: 'task-poll',
        status: 'pending' as const,
        progress: 0,
        message: 'Starting',
        total_files: 10,
        processed_files: 0,
        total_chunks: 0,
        created_at: new Date().toISOString(),
      }

      const mockStatus2 = {
        task_id: 'task-poll',
        status: 'running' as const,
        progress: 50,
        message: 'Processing',
        total_files: 10,
        processed_files: 5,
        total_chunks: 50,
        created_at: new Date().toISOString(),
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)
      vi.mocked(api.getIndexStatus)
        .mockResolvedValueOnce(mockStatus1)
        .mockResolvedValueOnce(mockStatus2)

      // Force polling
      mockWebSocket.connect.mockImplementation(() => {
        throw new Error('WS failed')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const store = useIndexStore()
      await store.start('/path/to/files')

      // First poll happens immediately in startPolling - wait for it
      // With fake timers, we need to flush pending promises
      await vi.waitFor(() => {
        expect(api.getIndexStatus).toHaveBeenCalledWith('task-poll')
      })
      expect(store.currentTask?.status).toBe('pending')

      // Advance timers for the second poll
      await vi.advanceTimersByTimeAsync(1000)
      expect(store.currentTask?.status).toBe('running')

      consoleSpy.mockRestore()
    })

    it('should stop polling when task completes', async () => {
      const mockResponse = {
        task_id: 'task-poll-complete',
        message: 'Indexing started',
        status_url: '/api/index/status/task-poll-complete',
      }

      const mockStatusComplete = {
        task_id: 'task-poll-complete',
        status: 'completed' as const,
        progress: 100,
        message: 'Done',
        total_files: 10,
        processed_files: 10,
        total_chunks: 100,
        created_at: new Date().toISOString(),
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)
      vi.mocked(api.getIndexStatus).mockResolvedValue(mockStatusComplete)

      // Force polling
      mockWebSocket.connect.mockImplementation(() => {
        throw new Error('WS failed')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const store = useIndexStore()
      await store.start('/path/to/files')

      // First poll completes the task
      vi.advanceTimersByTime(1000)
      await Promise.resolve()

      expect(store.currentTask?.status).toBe('completed')

      // Clear to check no more calls
      vi.mocked(api.getIndexStatus).mockClear()

      // Advance time - should not poll anymore for completed task
      vi.advanceTimersByTime(2000)
      expect(api.getIndexStatus).not.toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('should handle polling error', async () => {
      const mockResponse = {
        task_id: 'task-poll-err',
        message: 'Indexing started',
        status_url: '/api/index/status/task-poll-err',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)
      vi.mocked(api.getIndexStatus).mockRejectedValue(new Error('Network error'))
      vi.mocked(getErrorMessage).mockReturnValue('Network error')

      // Force polling
      mockWebSocket.connect.mockImplementation(() => {
        throw new Error('WS failed')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Trigger polling
      vi.advanceTimersByTime(1000)
      await Promise.resolve()

      expect(consoleErrorSpy).toHaveBeenCalledWith('Polling error:', expect.any(Error))
      expect(store.error).toBe('Network error')

      consoleSpy.mockRestore()
      consoleErrorSpy.mockRestore()
    })
  })

  describe('cleanup on unmount', () => {
    it('should cleanup resources on unmount', async () => {
      const mockResponse = {
        task_id: 'task-unmount',
        message: 'Indexing started',
        status_url: '/api/index/status/task-unmount',
      }

      vi.mocked(api.startIndex).mockResolvedValue(mockResponse)

      const store = useIndexStore()
      await store.start('/path/to/files')

      // Simulate unmount
      expect(onUnmountedCallbacks).toHaveLength(1)
      onUnmountedCallbacks[0]()

      expect(mockWebSocket.disconnect).toHaveBeenCalled()
    })
  })
})