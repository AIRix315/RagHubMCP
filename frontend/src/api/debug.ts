/**
 * Debug API
 * 
 * 根据 Docs/23-UI-Plan.md 定义
 * 用于调试 Pipeline 和 Search Test
 */

import apiClient from './client'
import type { DebugInfo, SearchTestRequest, SearchTestResponse } from '@/types/debug'

// ========== Search Test API ==========

/**
 * 执行搜索测试
 */
export async function searchTest(
  request: SearchTestRequest
): Promise<SearchTestResponse> {
  const { data } = await apiClient.post<SearchTestResponse>('/query', {
    query: request.query,
    collection: request.collection || 'default',
    top_k: request.top_k || 10,
    profile: request.profile,
    enable_rerank: request.enable_rerank ?? true,
    debug: request.debug ?? false
  })
  return data
}

/**
 * 获取调试信息
 */
export async function getDebugInfo(queryId: string): Promise<DebugInfo> {
  const { data } = await apiClient.get<DebugInfo>(`/debug/${queryId}`)
  return data
}

// ========== Index Task API (补充) ==========

/**
 * 获取索引任务列表
 */
export async function listIndexTasks(): Promise<IndexTask[]> {
  const { data } = await apiClient.get<IndexTask[]>('/indexing/tasks')
  return data
}

/**
 * 获取索引任务状态
 */
export async function getIndexStatus(taskId: string): Promise<IndexTaskStatus> {
  const { data } = await apiClient.get<IndexTaskStatus>(`/indexing/tasks/${taskId}`)
  return data
}

// ========== Types ==========

export interface IndexTask {
  task_id: string
  path: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  created_at: string
  completed_at?: string
}

export interface IndexTaskStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  progress: number
  message: string
  total_files: number
  processed_files: number
  total_chunks: number
  error?: string
  created_at: string
  completed_at?: string
}