import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { CollectionsListResponse, CollectionInfo } from '@/types'
import { listCollections, deleteCollection } from '@/api'

export const useCollectionStore = defineStore('collection', () => {
  const collections = ref<CollectionInfo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Computed statistics
  const totalCollections = computed(() => collections.value.length)
  
  const totalDocuments = computed(() =>
    collections.value.reduce((sum, col) => sum + col.count, 0)
  )
  
  const averageDocumentsPerCollection = computed(() => {
    if (totalCollections.value === 0) return 0
    return Math.round(totalDocuments.value / totalCollections.value)
  })

  async function loadCollections() {
    loading.value = true
    error.value = null
    try {
      const response: CollectionsListResponse = await listCollections()
      collections.value = response.collections
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load collections'
    } finally {
      loading.value = false
    }
  }

  async function removeCollection(name: string) {
    loading.value = true
    error.value = null
    try {
      await deleteCollection(name)
      await loadCollections()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete collection'
    } finally {
      loading.value = false
    }
  }

  return {
    collections,
    loading,
    error,
    lastUpdated,
    // Computed stats
    totalCollections,
    totalDocuments,
    averageDocumentsPerCollection,
    // Actions
    loadCollections,
    removeCollection,
  }
})