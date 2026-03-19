import apiClient from './client'
import type { SearchRequest, SearchResponse, CollectionsListResponse } from '@/types'

/**
 * Execute a search query
 * TC-1.15.5: POST /api/search executes search
 */
export async function executeSearch(request: SearchRequest): Promise<SearchResponse> {
  const response = await apiClient.post<SearchResponse>('/search', request)
  return response.data
}

/**
 * List all collections
 */
export async function listCollections(): Promise<CollectionsListResponse> {
  const response = await apiClient.get<CollectionsListResponse>('/search/collections')
  return response.data
}

/**
 * Delete a collection
 */
export async function deleteCollection(name: string): Promise<{ name: string; message: string }> {
  const response = await apiClient.delete<{ name: string; message: string }>(`/search/collections/${name}`)
  return response.data
}