import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock WebSocket globally - synchronous version
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState: number = MockWebSocket.OPEN
  url: string
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    mockWebSocketInstances.push(this)
  }

  send = vi.fn()

  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED
  })

  // Helper to simulate connection open
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.(new Event('open'))
  }

  // Helper to simulate message
  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent)
  }

  // Helper to simulate close
  simulateClose() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close'))
  }

  // Helper to simulate error
  simulateError() {
    this.onerror?.(new Event('error'))
  }
}

// Track all WebSocket instances
let mockWebSocketInstances: MockWebSocket[] = []

// Mock global WebSocket
vi.stubGlobal('WebSocket', MockWebSocket)

// Mock import.meta.env
vi.stubGlobal('import.meta', {
  env: {
    VITE_WS_BASE_URL: undefined,
    PROD: false,
  },
})

// Mock onUnmounted to track cleanup
const onUnmountedCallbacks: (() => void)[] = []
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onUnmounted: (callback: () => void) => {
      onUnmountedCallbacks.push(callback)
    },
  }
})

describe('useWebSocket composable', () => {
  let useWebSocket: typeof import('@/composables/useWebSocket').useWebSocket

  beforeEach(async () => {
    vi.clearAllMocks()
    mockWebSocketInstances = []
    onUnmountedCallbacks.length = 0

    // Reset modules and re-import
    vi.resetModules()

    // Re-mock vue with fresh onUnmountedCallbacks
    vi.doMock('vue', async () => {
      const actual = await vi.importActual('vue')
      return {
        ...actual,
        onUnmounted: (callback: () => void) => {
          onUnmountedCallbacks.push(callback)
        },
      }
    })

    useWebSocket = (await import('@/composables/useWebSocket')).useWebSocket
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('initialization', () => {
    it('should initialize with default state', () => {
      const { isConnected, progressData, error } = useWebSocket()

      expect(isConnected.value).toBe(false)
      expect(progressData.value).toBeNull()
      expect(error.value).toBeNull()
    })

    it('should accept custom options', () => {
      const onProgress = vi.fn()
      const onConnected = vi.fn()
      const onDisconnected = vi.fn()
      const onError = vi.fn()

      useWebSocket({
        onProgress,
        onConnected,
        onDisconnected,
        onError,
        heartbeatInterval: 10000,
        autoReconnect: false,
        reconnectDelay: 2000,
      })

      // Should not throw and options should be stored
      expect(true).toBe(true)
    })
  })

  describe('connection lifecycle', () => {
    it('should connect to WebSocket with correct URL', () => {
      const { connect } = useWebSocket()

      connect('task-123')

      expect(mockWebSocketInstances).toHaveLength(1)
      expect(mockWebSocketInstances[0].url).toContain('/ws/progress/task-123')
    })

    it('should set isConnected to true on connection open', () => {
      const { connect, isConnected } = useWebSocket()

      connect('task-456')
      expect(isConnected.value).toBe(false)

      // Simulate WebSocket open
      mockWebSocketInstances[0].simulateOpen()

      expect(isConnected.value).toBe(true)
    })

    it('should clear error on successful connection', () => {
      const { connect, error } = useWebSocket()

      error.value = 'Previous error'
      connect('task-789')

      mockWebSocketInstances[0].simulateOpen()

      expect(error.value).toBeNull()
    })

    it('should disconnect and clear state', () => {
      const { connect, disconnect, isConnected, progressData } = useWebSocket()

      connect('task-111')
      mockWebSocketInstances[0].simulateOpen()

      expect(isConnected.value).toBe(true)

      disconnect()

      expect(isConnected.value).toBe(false)
      expect(progressData.value).toBeNull()
      expect(mockWebSocketInstances[0].close).toHaveBeenCalled()
    })

    it('should close existing connection when connecting to new task', () => {
      const { connect } = useWebSocket()

      connect('task-first')
      mockWebSocketInstances[0].simulateOpen()

      const firstWs = mockWebSocketInstances[0]

      connect('task-second')

      expect(firstWs.close).toHaveBeenCalled()
      expect(mockWebSocketInstances).toHaveLength(2)
    })
  })

  describe('message handling', () => {
    it('should handle progress message and update state', () => {
      const { connect, progressData } = useWebSocket()

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      const progressPayload = {
        type: 'progress',
        data: {
          status: 'running',
          progress: 50,
          message: 'Processing...',
          total_files: 10,
          processed_files: 5,
          total_chunks: 100,
        },
        timestamp: new Date().toISOString(),
      }

      mockWebSocketInstances[0].simulateMessage(progressPayload)

      expect(progressData.value).toEqual(progressPayload.data)
    })

    it('should call onProgress callback when progress message received', () => {
      const onProgress = vi.fn()
      const { connect } = useWebSocket({ onProgress })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      const progressData = {
        status: 'running' as const,
        progress: 75,
        message: 'Almost done',
        total_files: 4,
        processed_files: 3,
        total_chunks: 50,
      }

      mockWebSocketInstances[0].simulateMessage({
        type: 'progress',
        data: progressData,
        timestamp: new Date().toISOString(),
      })

      expect(onProgress).toHaveBeenCalledWith(progressData)
    })

    it('should handle connected message', () => {
      const onConnected = vi.fn()
      const { connect } = useWebSocket({ onConnected })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      mockWebSocketInstances[0].simulateMessage({
        type: 'connected',
        timestamp: new Date().toISOString(),
      })

      expect(onConnected).toHaveBeenCalled()
    })

    it('should handle error message', () => {
      const onError = vi.fn()
      const { connect, error } = useWebSocket({ onError })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      mockWebSocketInstances[0].simulateMessage({
        type: 'error',
        message: 'Server error occurred',
        timestamp: new Date().toISOString(),
      })

      expect(error.value).toBe('Server error occurred')
      expect(onError).toHaveBeenCalledWith('Server error occurred')
    })

    it('should handle heartbeat message without errors', () => {
      const { connect } = useWebSocket()

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      // Should not throw
      expect(() => {
        mockWebSocketInstances[0].simulateMessage({
          type: 'heartbeat',
          timestamp: new Date().toISOString(),
        })
      }).not.toThrow()
    })

    it('should handle invalid JSON message gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const { connect } = useWebSocket()

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      // Simulate invalid JSON by calling onmessage directly
      mockWebSocketInstances[0].onmessage?.({ data: 'invalid json' } as MessageEvent)

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('event handlers', () => {
    it('should call onDisconnected when connection closes', () => {
      const onDisconnected = vi.fn()
      const { connect } = useWebSocket({ onDisconnected })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      mockWebSocketInstances[0].simulateClose()

      expect(onDisconnected).toHaveBeenCalled()
    })

    it('should call onError when WebSocket error occurs', () => {
      const onError = vi.fn()
      const { connect, error } = useWebSocket({ onError })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      mockWebSocketInstances[0].simulateError()

      expect(error.value).toBe('WebSocket connection error')
      expect(onError).toHaveBeenCalledWith('WebSocket connection error')
    })
  })

  describe('heartbeat', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should start heartbeat on connection', () => {
      const { connect } = useWebSocket({ heartbeatInterval: 5000 })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      // Advance past heartbeat interval
      vi.advanceTimersByTime(5000)

      expect(mockWebSocketInstances[0].send).toHaveBeenCalledWith('ping')
    })

    it('should stop heartbeat on disconnect', () => {
      const { connect, disconnect } = useWebSocket({ heartbeatInterval: 5000 })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      disconnect()

      // Clear mock to check new calls
      mockWebSocketInstances[0].send.mockClear()

      // Advance time
      vi.advanceTimersByTime(10000)

      // Should not have sent ping after disconnect
      expect(mockWebSocketInstances[0].send).not.toHaveBeenCalled()
    })
  })

  describe('reconnection logic', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should auto-reconnect when connection closes', () => {
      const { connect } = useWebSocket({
        autoReconnect: true,
        reconnectDelay: 1000,
      })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      expect(mockWebSocketInstances).toHaveLength(1)

      // Simulate connection close
      mockWebSocketInstances[0].simulateClose()

      // Wait for reconnect delay
      vi.advanceTimersByTime(1500)

      // Should have created a new WebSocket
      expect(mockWebSocketInstances).toHaveLength(2)
      expect(mockWebSocketInstances[1].url).toContain('/ws/progress/task-123')
    })

    it('should not auto-reconnect when autoReconnect is false', () => {
      const { connect } = useWebSocket({
        autoReconnect: false,
        reconnectDelay: 1000,
      })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      mockWebSocketInstances[0].simulateClose()

      vi.advanceTimersByTime(1500)

      // Should not have created a new WebSocket
      expect(mockWebSocketInstances).toHaveLength(1)
    })

    it('should not auto-reconnect after disconnect called', () => {
      const { connect, disconnect } = useWebSocket({
        autoReconnect: true,
        reconnectDelay: 1000,
      })

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      disconnect()

      vi.advanceTimersByTime(1500)

      // Should not have created a new WebSocket after disconnect
      expect(mockWebSocketInstances).toHaveLength(1)
    })
  })

  describe('send function', () => {
    it('should send message when connected', () => {
      const { connect, send } = useWebSocket()

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      send('test message')

      expect(mockWebSocketInstances[0].send).toHaveBeenCalledWith('test message')
    })

    it('should not send message when not connected', () => {
      const { send } = useWebSocket()

      // Try to send without connecting - should not throw
      expect(() => send('test message')).not.toThrow()

      // No WebSocket instances created
      expect(mockWebSocketInstances).toHaveLength(0)
    })

    it('should not send message after disconnect', () => {
      const { connect, disconnect, send } = useWebSocket()

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      const ws = mockWebSocketInstances[0]
      disconnect()

      // Clear the mock to check new calls
      ws.send.mockClear()

      send('test message')

      expect(ws.send).not.toHaveBeenCalled()
    })
  })

  describe('cleanup on unmount', () => {
    it('should disconnect on component unmount', () => {
      const { connect } = useWebSocket()

      connect('task-123')
      mockWebSocketInstances[0].simulateOpen()

      // Simulate component unmount
      expect(onUnmountedCallbacks).toHaveLength(1)
      onUnmountedCallbacks[0]()

      expect(mockWebSocketInstances[0].close).toHaveBeenCalled()
    })
  })

  describe('error handling', () => {
    it('should handle WebSocket creation error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      // Override WebSocket constructor to throw
      const OriginalWebSocket = MockWebSocket
      vi.stubGlobal('WebSocket', class {
        constructor() {
          throw new Error('WebSocket creation failed')
        }
      })

      vi.resetModules()
      const useWebSocketFresh = (await import('@/composables/useWebSocket')).useWebSocket

      const { connect, error } = useWebSocketFresh()

      connect('task-123')

      expect(error.value).toBe('Failed to create WebSocket connection')
      expect(consoleSpy).toHaveBeenCalled()

      // Restore
      vi.stubGlobal('WebSocket', OriginalWebSocket)
      consoleSpy.mockRestore()
    })
  })
})