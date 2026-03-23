/**
 * Pipeline Types
 * 
 * 根据 Docs/23-UI-Plan.md 定义
 * 包含 Pipeline 各阶段的配置类型
 */

import type { RankStrategy, RankStrategyConfig } from './provider'

// ========== Pipeline 状态 ==========

export type PipelineStageStatus = 'pending' | 'running' | 'completed' | 'error'

// ========== Retrieval Stage ==========

export interface HybridSearchConfig {
  enabled: boolean
  vector_weight: number
  bm25_weight: number
}

export interface RetrievalConfig {
  top_k: number
  hybrid?: HybridSearchConfig
}

// ========== Rerank Stage ==========

export interface RerankStageConfig {
  enabled: boolean
  provider: string
  top_k: number
  score_threshold: number
  strategy: RankStrategy
  strategy_config?: RankStrategyConfig
}

// ========== Context Builder Stage ==========

export type ReorderingMethod = 'chronological' | 'relevance' | 'original'

export interface ContextBuilderConfig {
  enabled: boolean
  max_tokens: number
  deduplicate: boolean
  deduplication_threshold: number
  merge_continuous: boolean
  reordering: ReorderingMethod
}

// ========== Pipeline 完整配置 ==========

export interface PipelineConfig {
  default_profile: string
  retrieval: RetrievalConfig
  rerank: RerankStageConfig
  context_builder: ContextBuilderConfig
}

// ========== Pipeline 更新响应 ==========

export interface PipelineUpdateResponse {
  config: PipelineConfig
  requires_restart: string[]
}