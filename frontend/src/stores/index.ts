import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { IndexTaskStatus } from '@/types'
import { startIndex, getIndexStatus } from '@/api'

export const useIndexStore = defineStore('index', () => {
  const tasks = ref<IndexTaskStatus[]>([])
  const currentTask = ref<IndexTaskStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function start(path: string, collectionName = 'default') {
    loading.value = true
    error.value = null
    try {
      const response = await startIndex({
        path,
        collection_name: collectionName,
      })
      // Poll for status
      await pollStatus(response.task_id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start indexing'
    } finally {
      loading.value = false
    }
  }

  async function pollStatus(taskId: string) {
    const poll = async () => {
      const status = await getIndexStatus(taskId)
      currentTask.value = status
      
      if (status.status === 'pending' || status.status === 'running') {
        setTimeout(poll, 1000)
      }
    }
    await poll()
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    start,
    pollStatus,
  }
})