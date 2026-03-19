/**
 * Configuration types matching backend/src/api/schemas.py
 */

export interface ServerConfig {
  host: string
  port: number
  debug: boolean
}

export interface ChromaConfig {
  persist_dir: string
  host: string | null
  port: number | null
}

export interface ProviderInstance {
  name: string
  type: string
  model: string
  base_url?: string | null
  dimension?: number | null
}

export interface ProviderCategory {
  default: string
  instances: ProviderInstance[]
}

export interface ProvidersConfig {
  embedding: ProviderCategory
  rerank: ProviderCategory
  llm: ProviderCategory
}

export interface IndexerConfig {
  chunk_size: number
  chunk_overlap: number
  max_file_size: number
  file_types: string[]
  exclude_dirs: string[]
}

export interface LoggingConfig {
  level: string
  format: string
  file: string | null
}

export interface ConfigModel {
  server: ServerConfig
  chroma: ChromaConfig
  providers: ProvidersConfig
  indexer: IndexerConfig
  logging: LoggingConfig
}

export interface ConfigUpdateRequest {
  server?: ServerConfig
  chroma?: ChromaConfig
  providers?: ProvidersConfig
  indexer?: IndexerConfig
  logging?: LoggingConfig
}