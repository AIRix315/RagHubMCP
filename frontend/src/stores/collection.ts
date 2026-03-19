import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { CollectionsListResponse, CollectionInfo } from '@/types'
import { listCollections, deleteCollection } from '@/api'

export const useCollectionStore = defineStore('collection', () => {
  const collections = ref<CollectionInfo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadCollections() {
    loading.value = true
    error.value = null
    try {
      const response: CollectionsListResponse = await listCollections()
      collections.value = response.collections
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
    loadCollections,
    removeCollection,
  }
})