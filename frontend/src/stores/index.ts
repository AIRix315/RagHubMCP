import { ref, onUnmounted } from 'vue'
import { defineStore } from 'pinia'
import type { IndexTaskStatus } from '@/types'
import { startIndex, getIndexStatus } from '@/api'
import { useWebSocket, type ProgressData } from '@/composables/useWebSocket'

export const useIndexStore = defineStore('index', () => {
  const tasks = ref<IndexTaskStatus[]>([])
  const currentTask = ref<IndexTaskStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const isConnected = ref(false)

  // WebSocket instance for real-time updates
  const {
    isConnected: wsConnected,
    progressData,
    connect: wsConnect,
    disconnect: wsDisconnect,
  } = useWebSocket({
    onProgress: handleProgressUpdate,
    onConnected: () => {
      isConnected.value = true
    },
    onDisconnected: () => {
      isConnected.value = false
    },
    onError: (errorMsg) => {
      console.error('WebSocket error:', errorMsg)
      // Fall back to polling on error
      if (currentTask.value?.task_id) {
        startPolling(currentTask.value.task_id)
      }
    },
  })

  /**
   * Handle progress update from WebSocket
   */
  function handleProgressUpdate(data: ProgressData) {
    if (currentTask.value) {
      currentTask.value = {
        ...currentTask.value,
        status: data.status,
        progress: data.progress,
        message: data.message,
        total_files: data.total_files,
        processed_files: data.processed_files,
        total_chunks: data.total_chunks,
        error: data.error,
      }

      // If task is completed or failed, disconnect WebSocket
      if (data.status === 'completed' || data.status === 'failed') {
        wsDisconnect()
      }
    }
  }

  /**
   * Start indexing a path
   */
  async function start(path: string, collectionName = 'default') {
    loading.value = true
    error.value = null
    try {
      const response = await startIndex({
        path,
        collection_name: collectionName,
      })
      
      // Initialize task
      currentTask.value = {
        task_id: response.task_id,
        status: 'pending',
        progress: 0,
        message: 'Task created, waiting to start',
        total_files: 0,
        processed_files: 0,
        total_chunks: 0,
        created_at: new Date().toISOString(),
      }

      // Try WebSocket first
      try {
        wsConnect(response.task_id)
      } catch (e) {
        console.warn('WebSocket connection failed, falling back to polling:', e)
        // Fall back to polling
        startPolling(response.task_id)
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start indexing'
    } finally {
      loading.value = false
    }
  }

  /**
   * Poll for status updates (fallback)
   */
  let pollingTimer: ReturnType<typeof setTimeout> | null = null

  function startPolling(taskId: string) {
    stopPolling()
    
    const poll = async () => {
      try {
        const status = await getIndexStatus(taskId)
        currentTask.value = status
        
        if (status.status === 'pending' || status.status === 'running') {
          pollingTimer = setTimeout(poll, 1000)
        }
      } catch (e) {
        console.error('Polling error:', e)
        error.value = e instanceof Error ? e.message : 'Failed to get status'
      }
    }
    
    poll()
  }

  function stopPolling() {
    if (pollingTimer) {
      clearTimeout(pollingTimer)
      pollingTimer = null
    }
  }

  /**
   * Get task status via REST API
   */
  async function getStatus(taskId: string) {
    try {
      const status = await getIndexStatus(taskId)
      currentTask.value = status
      return status
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to get status'
      throw e
    }
  }

  /**
   * Stop monitoring current task
   */
  function stopMonitoring() {
    wsDisconnect()
    stopPolling()
    currentTask.value = null
  }

  /**
   * Clear current task
   */
  function clearCurrentTask() {
    stopMonitoring()
    error.value = null
  }

  // Cleanup on store disposal
  onUnmounted(() => {
    stopMonitoring()
  })

  return {
    tasks,
    currentTask,
    loading,
    error,
    isConnected,
    start,
    getStatus,
    stopMonitoring,
    clearCurrentTask,
    // Exposed for backward compatibility
    pollStatus: startPolling,
  }
})