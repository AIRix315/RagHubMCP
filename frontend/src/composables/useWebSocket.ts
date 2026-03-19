/**
 * WebSocket composable for real-time progress updates.
 * 
 * Provides reactive WebSocket connection management with automatic
 * reconnection and heartbeat support.
 */

import { ref, onUnmounted, type Ref } from 'vue'

export interface ProgressData {
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  total_files: number
  processed_files: number
  total_chunks: number
  error?: string | null
}

export interface WebSocketMessage {
  type: 'progress' | 'heartbeat' | 'error' | 'connected'
  task_id?: string
  data?: ProgressData
  message?: string
  timestamp: string
}

export interface UseWebSocketOptions {
  /** Callback when progress is received */
  onProgress?: (data: ProgressData) => void
  /** Callback when connection is established */
  onConnected?: () => void
  /** Callback when connection is closed */
  onDisconnected?: () => void
  /** Callback when error occurs */
  onError?: (error: string) => void
  /** Heartbeat interval in milliseconds (default: 30000) */
  heartbeatInterval?: number
  /** Auto reconnect on disconnect (default: true) */
  autoReconnect?: boolean
  /** Reconnect delay in milliseconds (default: 1000) */
  reconnectDelay?: number
}

export interface UseWebSocketReturn {
  /** Connection status */
  isConnected: Ref<boolean>
  /** Last received progress data */
  progressData: Ref<ProgressData | null>
  /** Last error message */
  error: Ref<string | null>
  /** Connect to WebSocket for a specific task */
  connect: (taskId: string) => void
  /** Disconnect WebSocket */
  disconnect: () => void
  /** Send message to server */
  send: (message: string) => void
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 
  (import.meta.env.PROD ? 'wss://' + window.location.host : 'ws://localhost:8000')

/**
 * Composable for WebSocket-based real-time progress updates.
 * 
 * @param options - Configuration options
 * @returns WebSocket controls and state
 * 
 * @example
 * ```ts
 * const { isConnected, progressData, connect, disconnect } = useWebSocket({
 *   onProgress: (data) => console.log('Progress:', data.progress),
 * })
 * 
 * // Connect to a task
 * connect('task-123')
 * 
 * // Later, disconnect
 * disconnect()
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onProgress,
    onConnected,
    onDisconnected,
    onError,
    heartbeatInterval = 30000,
    autoReconnect = true,
    reconnectDelay = 1000,
  } = options

  const isConnected = ref(false)
  const progressData = ref<ProgressData | null>(null)
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let currentTaskId: string | null = null

  /**
   * Start heartbeat to keep connection alive
   */
  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, heartbeatInterval)
  }

  /**
   * Stop heartbeat
   */
  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  function handleMessage(event: MessageEvent) {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)

      switch (message.type) {
        case 'progress':
          if (message.data) {
            progressData.value = message.data
            onProgress?.(message.data)
          }
          break

        case 'connected':
          onConnected?.()
          break

        case 'error':
          error.value = message.message || 'Unknown error'
          onError?.(error.value)
          break

        case 'heartbeat':
          // Server responded to ping, connection is alive
          break
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }

  /**
   * Handle WebSocket open event
   */
  function handleOpen() {
    isConnected.value = true
    error.value = null
    startHeartbeat()
  }

  /**
   * Handle WebSocket close event
   */
  function handleClose() {
    isConnected.value = false
    stopHeartbeat()
    onDisconnected?.()

    // Auto reconnect if enabled and we have a task ID
    if (autoReconnect && currentTaskId) {
      scheduleReconnect(currentTaskId)
    }
  }

  /**
   * Handle WebSocket error event
   */
  function handleError(event: Event) {
    const errorMsg = 'WebSocket connection error'
    error.value = errorMsg
    console.error(errorMsg, event)
    onError?.(errorMsg)
  }

  /**
   * Schedule a reconnection attempt
   */
  function scheduleReconnect(_taskId: string) {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }
    reconnectTimer = setTimeout(() => {
      if (currentTaskId) {
        connectInternal(currentTaskId)
      }
    }, reconnectDelay)
  }

  /**
   * Internal connect implementation
   */
  function connectInternal(taskId: string) {
    // Close existing connection
    if (ws) {
      ws.close()
    }

    currentTaskId = taskId
    const wsUrl = `${WS_BASE_URL}/ws/progress/${taskId}`

    try {
      ws = new WebSocket(wsUrl)
      ws.onopen = handleOpen
      ws.onmessage = handleMessage
      ws.onclose = handleClose
      ws.onerror = handleError
    } catch (e) {
      error.value = 'Failed to create WebSocket connection'
      console.error('WebSocket creation error:', e)
    }
  }

  /**
   * Connect to WebSocket for a specific task
   */
  function connect(taskId: string) {
    // Clear any pending reconnect
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    connectInternal(taskId)
  }

  /**
   * Disconnect WebSocket
   */
  function disconnect() {
    // Clear task ID to prevent auto-reconnect
    currentTaskId = null
    
    // Clear reconnect timer
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    stopHeartbeat()
    
    if (ws) {
      ws.close()
      ws = null
    }
    
    isConnected.value = false
    progressData.value = null
  }

  /**
   * Send message to server
   */
  function send(message: string) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(message)
    }
  }

  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    progressData,
    error,
    connect,
    disconnect,
    send,
  }
}

export default useWebSocket