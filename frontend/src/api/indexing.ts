import apiClient from './client'
import type { IndexRequest, IndexResponse, IndexTaskStatus } from '@/types'

/**
 * Start an indexing task
 * TC-1.15.3: POST /api/index starts indexing
 */
export async function startIndex(request: IndexRequest): Promise<IndexResponse> {
  const response = await apiClient.post<IndexResponse>('/index', request)
  return response.data
}

/**
 * Get indexing task status
 * TC-1.15.4: GET /api/index/status queries status
 */
export async function getIndexStatus(taskId: string): Promise<IndexTaskStatus> {
  const response = await apiClient.get<IndexTaskStatus>(`/index/status/${taskId}`)
  return response.data
}

/**
 * List all indexing tasks
 */
export async function listIndexTasks(): Promise<IndexTaskStatus[]> {
  const response = await apiClient.get<IndexTaskStatus[]>('/index/status')
  return response.data
}