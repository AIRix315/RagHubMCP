/**
 * Debug Types
 * 
 * 根据 Docs/23-UI-Plan.md 定义
 * 用于 Pipeline 调试和中间状态查看
 */

// ========== Debug Stage Input ==========

export interface RetrievalInput {
  query: string
  collection?: string
}

export interface RerankInput {
  candidates_count: number
}

export interface ContextBuilderInput {
  ranked_count: number
}

export interface DebugStageInput {
  retrieval?: RetrievalInput
  rerank?: RerankInput
  context_builder?: ContextBuilderInput
}

// ========== Debug Stage Output ==========

export interface RetrievalOutput {
  candidates_count: number
  vector_candidates?: number
  bm25_candidates?: number
}

export interface RerankScoreDetail {
  doc_id: string
  retrieval_score: number
  rerank_score: number
  final_score: number
  position: number
  blend_ratio?: [number, number]
}

export interface RerankOutput {
  ranked_count: number
  scores?: RerankScoreDetail[]
}

export interface ContextBuilderOutput {
  final_count: number
  deduplicated_count: number
  merged_chunks: number
  final_tokens: number
}

export interface DebugStageOutput {
  retrieval?: RetrievalOutput
  rerank?: RerankOutput
  context_builder?: ContextBuilderOutput
}

// ========== Debug Stage Metadata ==========

export interface RetrievalMetadata {
  strategy: string
  latency_ms: number
}

export interface RerankMetadata {
  engine: string
  strategy: string
  threshold: number
  latency_ms: number
}

export interface ContextBuilderMetadata {
  deduplication_threshold: number
  latency_ms: number
}

export interface DebugStageMetadata {
  retrieval?: RetrievalMetadata
  rerank?: RerankMetadata
  context_builder?: ContextBuilderMetadata
}

// ========== Debug Stage ==========

export interface DebugStage {
  name: string
  status: 'pending' | 'running' | 'completed' | 'error'
  input: DebugStageInput
  output: DebugStageOutput
  latency_ms: number
  metadata: DebugStageMetadata
}

// ========== Debug Info (完整响应) ==========

export interface DebugInfo {
  query_id: string
  stages: DebugStage[]
  total_latency_ms: number
}

// ========== Search Test 相关 ==========

export interface SearchTestResult {
  id: string
  title: string
  source: string
  content: string
  score: number
  rank: number
  metadata?: Record<string, unknown>
}

export interface SearchTestRequest {
  query: string
  collection?: string
  top_k?: number
  profile?: string
  enable_rerank?: boolean
  debug?: boolean
}

export interface SearchTestResponse {
  results: SearchTestResult[]
  total_count: number
  latency_ms: number
  query_id?: string
  debug_info?: DebugInfo
}