/**
 * Provider types matching backend/src/api/schemas.py
 * Provider Management types for embedding, rerank, llm, vectorstore
 */

// =============================================================================
// Provider Status and Types
// =============================================================================

export type ProviderType = 'embedding' | 'rerank' | 'llm' | 'vectorstore'

export type ProviderStatus = 'active' | 'inactive' | 'error'

export type RerankEngineType = 'cross_encoder' | 'colbert' | 'bge_reranker' | 'position_aware_blending'

// =============================================================================
// Provider Info
// =============================================================================

export interface ProviderInfo {
  name: string
  type: string
  status: ProviderStatus
  is_default: boolean
  model?: string | null
  config?: Record<string, any>
  error_message?: string | null
  capabilities?: {
    supports_batch?: boolean
    has_model?: boolean
    [key: string]: any
  }
}

export interface ProvidersListResponse {
  embedding: ProviderInfo[]
  rerank: ProviderInfo[]
  llm: ProviderInfo[]
  vectorstore: ProviderInfo[]
}

// =============================================================================
// Provider CRUD
// =============================================================================

export interface ProviderCreateRequest {
  type: string
  config: Record<string, any>
  set_as_default?: boolean
}

export interface ProviderUpdateResponse {
  name: string
  message: string
  is_new: boolean
}

export interface ProviderDeleteResponse {
  name: string
  message: string
}

export interface SetDefaultProviderResponse {
  name: string
  type: string
  message: string
}

// =============================================================================
// Rerank Testing
// =============================================================================

export interface RerankResult {
  index: number
  text: string
  score: number
  rank: number
  processing_time_ms?: number | null
}

export interface RerankTestRequest {
  query: string
  documents: string[]
  top_k?: number
}

export interface RerankTestResponse {
  results: RerankResult[]
  latency_ms: number
  engine_info: {
    name: string
    type: string
    model: string
    [key: string]: any
  }
  intermediate_scores?: Record<string, number[]> | null
}

// =============================================================================
// Rerank Compare
// =============================================================================

export interface EngineMetrics {
  latency_ms: number
  top1_score: number
  avg_score: number
}

export interface EngineComparison {
  engine: string
  metrics: EngineMetrics
  results: RerankResult[]
}

export interface RerankCompareRequest {
  query: string
  documents: string[]
  engines: string[]
  top_k?: number
}

export interface RerankCompareResponse {
  query: string
  comparisons: EngineComparison[]
  total_latency_ms: number
}

// =============================================================================
// Rerank Engine Configurations
// =============================================================================

/** Cross Encoder配置 */
export interface CrossEncoderConfig {
  engine: 'cross_encoder'
  model_path: string
  max_length?: number
  batch_size?: number
  device?: 'cpu' | 'cuda' | 'auto'
}

/** ColBERT配置 */
export interface ColBERTConfig {
  engine: 'colbert'
  model_path: string
  dim?: number
  doc_maxlen?: number
  query_maxlen?: number
  use_gpu?: boolean
}

/** BGE Reranker配置 */
export interface BGERerankerConfig {
  engine: 'bge_reranker'
  model_name: string
  use_fp16?: boolean
  batch_size?: number
  normalize_scores?: boolean
}

/** Position-Aware Blending配置 */
export interface PositionAwareBlendingConfig {
  engine: 'position_aware_blending'
  weights: {
    semantic: number
    keyword: number
    position: number
  }
  position_decay?: number
  normalize?: boolean
}

export type RerankEngineConfig =
  | CrossEncoderConfig
  | ColBERTConfig
  | BGERerankerConfig
  | PositionAwareBlendingConfig

// =============================================================================
// Embedding Provider Configurations
// =============================================================================

export interface ONNXEmbeddingConfig {
  type: 'onnx'
  model_path: string
  dimension?: number
  max_length?: number
}

export interface OllamaEmbeddingConfig {
  type: 'ollama'
  model: string
  base_url?: string
  dimension?: number
}

export interface OpenAIEmbeddingConfig {
  type: 'openai'
  model: string
  api_key?: string
  base_url?: string
  dimension?: number
}

export type EmbeddingProviderConfig =
  | ONNXEmbeddingConfig
  | OllamaEmbeddingConfig
  | OpenAIEmbeddingConfig

// =============================================================================
// LLM Provider Configurations
// =============================================================================

export interface OllamaLLMConfig {
  type: 'ollama'
  model: string
  base_url?: string
  temperature?: number
  max_tokens?: number
}

export interface OpenAILLMConfig {
  type: 'openai'
  model: string
  api_key?: string
  base_url?: string
  temperature?: number
  max_tokens?: number
}

export type LLMProviderConfig = OllamaLLMConfig | OpenAILLMConfig

// =============================================================================
// VectorStore Provider Configurations
// =============================================================================

export interface ChromaVectorStoreConfig {
  type: 'chroma'
  persist_directory: string
  host?: string
  port?: number
}

export type VectorStoreProviderConfig = ChromaVectorStoreConfig
