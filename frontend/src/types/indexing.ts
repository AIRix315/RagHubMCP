/**
 * Index types matching backend/src/api/schemas.py
 */

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface IndexRequest {
  path: string
  collection_name?: string
  embedding_provider?: string | null
  chunk_size?: number | null
  chunk_overlap?: number | null
  recursive?: boolean
}

export interface IndexTaskStatus {
  task_id: string
  status: TaskStatus
  progress: number
  message: string
  total_files: number
  processed_files: number
  total_chunks: number
  created_at: string
  completed_at?: string | null
  error?: string | null
}

export interface IndexResponse {
  task_id: string
  message: string
  status_url: string
}