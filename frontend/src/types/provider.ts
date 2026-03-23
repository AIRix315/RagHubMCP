/**
 * Provider Types
 * 
 * 根据 Docs/23-UI-Plan.md 和 Docs/22-Config-API-Design.md 定义
 * 包含 Embedding、Rerank、VectorDB 三种 Provider 的完整类型
 */

// ========== 基础类型 ==========

export type ProviderType = 'embedding' | 'rerank' | 'vectordb'
export type ProviderStatus = 'active' | 'inactive' | 'error' | 'testing'
export type RerankEngineType = 'onnx' | 'api' | 'hybrid' | 'vector'
export type RankStrategy = 'standard' | 'position_aware' | 'diversity'
export type FusionMethod = 'linear' | 'rrf' | 'weighted_rrf'
export type NormalizeMethod = 'minmax' | 'softmax' | 'zscore'

// ========== Embedding Provider ==========

export type EmbeddingProviderType = 'ollama' | 'openai' | 'custom'

export interface OllamaEmbeddingConfig {
  base_url: string
  model: string
  dimension: number
}

export interface OpenAIEmbeddingConfig {
  api_key: string
  model: 'text-embedding-3-small' | 'text-embedding-3-large' | string
  dimension: number
}

export interface CustomEmbeddingConfig {
  base_url: string
  api_key?: string
  model: string
  dimension: number
}

export interface EmbeddingProviderConfig {
  name: string
  type: EmbeddingProviderType
  model: string
  dimension: number
  base_url?: string
  api_key?: string
  is_default?: boolean
  status?: ProviderStatus
}

// ========== Rerank Provider ==========

export interface ONNXConfig {
  model_path: string
  tokenizer_path: string
  max_length: number
  batch_size: number
  providers: string[]  // ['CPUExecutionProvider'] | ['CUDAExecutionProvider']
  score_threshold: number
}

export interface APIRerankConfig {
  base_url: string
  model: string
  api_key: string
  timeout: number
  max_retries: number
  rate_limit_per_minute: number
}

export interface HybridRerankConfig {
  vector_weight: number
  fusion_method: FusionMethod
  normalize_method: NormalizeMethod
  bm25_config: {
    k1: number
    b: number
  }
}

export interface VectorConfig {
  similarity_fn: 'cosine' | 'dot' | 'euclidean'
  embedding_provider: string
}

export interface PositionAwareConfig {
  blend_ratios: Record<string, [number, number]>
  // 示例: { "1-3": [0.75, 0.25], "4-10": [0.60, 0.40], "11+": [0.40, 0.60] }
}

export interface DiversityConfig {
  lambda_param: number  // 0.0-1.0
}

export interface RankStrategyConfig {
  position_aware?: PositionAwareConfig
  diversity?: DiversityConfig
}

export interface RerankProviderConfig {
  name: string
  type: RerankEngineType
  
  // 公共字段
  rank_strategy: RankStrategy
  strategy_config?: RankStrategyConfig
  
  // ONNX 特有
  onnx_config?: ONNXConfig
  
  // API 特有
  api_config?: APIRerankConfig
  
  // Hybrid 特有
  hybrid_config?: HybridRerankConfig
  
  // Vector 特有
  vector_config?: VectorConfig
  
  // 运行时状态
  is_default?: boolean
  status?: ProviderStatus
}

// ========== VectorDB Provider ==========

export type VectorDBType = 'chroma' | 'qdrant'

export interface ChromaProviderConfig {
  persist_dir: string
}

export interface QdrantProviderConfig {
  host: string
  port: number
  api_key?: string
  https?: boolean
}

export interface VectorDBProviderConfig {
  name: string
  type: VectorDBType
  
  // Chroma 特有
  persist_dir?: string
  
  // Qdrant 特有
  host?: string
  port?: number
  api_key?: string
  https?: boolean
  
  // 运行时状态
  is_default?: boolean
  status?: ProviderStatus
}

// ========== Provider 状态信息 ==========

export interface ProviderCapabilities {
  supports_batch: boolean
  supports_async: boolean
}

export interface ProviderStatusInfo {
  name: string
  type: string
  status: ProviderStatus
  model?: string
  config?: Record<string, unknown>
  is_default: boolean
  error_message?: string
  capabilities?: ProviderCapabilities
}

// ========== API 响应类型 ==========

export interface ProviderTestResponse {
  success: boolean
  latency_ms: number
  message: string
  details?: Record<string, unknown>
}

export interface ProviderListResponse {
  embedding: ProviderStatusInfo[]
  rerank: ProviderStatusInfo[]
  vectorstore: ProviderStatusInfo[]
}

// ========== Rerank Test Response ==========

export interface RerankTestResult {
  index: number
  text: string
  score: number
  rank: number
}

export interface RerankTestResponse {
  results: RerankTestResult[]
  latency_ms: number
  intermediate_scores?: {
    raw: number[]
    normalized: number[]
  }
}

export interface RerankComparisonItem {
  engine: string
  metrics: {
    ndcg: number
    mrr: number
    latency_ms: number
  }
  results: RerankTestResult[]
}

export interface RerankComparisonResponse {
  comparisons: RerankComparisonItem[]
}