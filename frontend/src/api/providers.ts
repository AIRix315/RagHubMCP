/**
 * Providers API
 * 
 * 根据 Docs/23-UI-Plan.md 定义
 * 包含 Embedding、Rerank、VectorDB Provider 的 API 调用
 */

import apiClient from './client'
import type {
  ProviderListResponse,
  ProviderStatusInfo,
  ProviderTestResponse,
  EmbeddingProviderConfig,
  RerankProviderConfig,
  VectorDBProviderConfig,
  RerankTestResponse,
  RerankComparisonResponse
} from '@/types/provider'

// ========== 通用 Provider API ==========

/**
 * 获取所有 Provider 列表
 */
export async function getProviders(): Promise<ProviderListResponse> {
  const { data } = await apiClient.get<ProviderListResponse>('/providers')
  return data
}

/**
 * 设置默认 Provider
 */
export async function setDefaultProvider(
  type: 'embedding' | 'rerank' | 'vectorstore',
  name: string
): Promise<void> {
  await apiClient.post(`/providers/${type}/${name}/set-default`)
}

/**
 * 删除 Provider
 */
export async function deleteProvider(
  type: 'embedding' | 'rerank' | 'vectorstore',
  name: string
): Promise<void> {
  await apiClient.delete(`/providers/${type}/${name}`)
}

// ========== Embedding Provider API ==========

/**
 * 获取所有 Embedding Provider
 */
export async function getEmbeddingProviders(): Promise<ProviderStatusInfo[]> {
  const { data } = await apiClient.get<ProviderStatusInfo[]>('/providers/embedding')
  return data
}

/**
 * 创建或更新 Embedding Provider
 */
export async function upsertEmbeddingProvider(
  config: EmbeddingProviderConfig
): Promise<ProviderStatusInfo> {
  const { data } = await apiClient.put<ProviderStatusInfo>(
    `/providers/embedding/${config.name}`,
    config
  )
  return data
}

/**
 * 测试 Embedding Provider
 */
export async function testEmbeddingProvider(
  name: string
): Promise<ProviderTestResponse> {
  const { data } = await apiClient.post<ProviderTestResponse>(
    `/providers/embedding/${name}/test`
  )
  return data
}

// ========== Rerank Provider API ==========

/**
 * 获取所有 Rerank Provider
 */
export async function getRerankProviders(): Promise<ProviderStatusInfo[]> {
  const { data } = await apiClient.get<ProviderStatusInfo[]>('/providers/rerank')
  return data
}

/**
 * 创建或更新 Rerank Provider
 */
export async function upsertRerankProvider(
  config: RerankProviderConfig
): Promise<ProviderStatusInfo> {
  const { data } = await apiClient.put<ProviderStatusInfo>(
    `/providers/rerank/${config.name}`,
    config
  )
  return data
}

/**
 * 测试 Rerank Provider
 */
export async function testRerankProvider(
  name: string,
  query: string,
  documents: string[],
  topK: number = 5
): Promise<RerankTestResponse> {
  const { data } = await apiClient.post<RerankTestResponse>(
    `/providers/rerank/${name}/test`,
    { query, documents, top_k: topK }
  )
  return data
}

/**
 * 对比多个 Rerank Provider
 */
export async function compareRerankProviders(
  query: string,
  documents: string[],
  engines: string[]
): Promise<RerankComparisonResponse> {
  const { data } = await apiClient.post<RerankComparisonResponse>(
    '/providers/rerank/compare',
    { query, documents, engines, metrics: ['ndcg', 'mrr', 'latency'] }
  )
  return data
}

// ========== VectorDB Provider API ==========

/**
 * 获取所有 VectorDB Provider
 */
export async function getVectorDBProviders(): Promise<ProviderStatusInfo[]> {
  const { data } = await apiClient.get<ProviderStatusInfo[]>('/providers/vectorstore')
  return data
}

/**
 * 创建或更新 VectorDB Provider
 */
export async function upsertVectorDBProvider(
  config: VectorDBProviderConfig
): Promise<ProviderStatusInfo> {
  const { data } = await apiClient.put<ProviderStatusInfo>(
    `/providers/vectorstore/${config.name}`,
    config
  )
  return data
}

/**
 * 测试 VectorDB Provider 连接
 */
export async function testVectorDBProvider(
  name: string
): Promise<ProviderTestResponse> {
  const { data } = await apiClient.post<ProviderTestResponse>(
    `/providers/vectorstore/${name}/test`
  )
  return data
}