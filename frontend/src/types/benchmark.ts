/**
 * Benchmark types matching backend/src/api/schemas.py
 */

import type { SearchResult } from './search'

export interface BenchmarkConfig {
  name: string
  embedding_provider: string
  rerank_provider?: string | null
  top_k?: number
}

export interface BenchmarkRequest {
  query: string
  collection_name?: string
  configs: BenchmarkConfig[]
}

export interface BenchmarkResult {
  config_name: string
  results: SearchResult[]
  latency_ms: number
  embedding_provider: string
  rerank_provider: string | null
}

export interface BenchmarkResponse {
  query: string
  collection: string
  results: BenchmarkResult[]
  total_latency_ms: number
}