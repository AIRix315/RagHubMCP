/**
 * Search types matching backend/src/api/schemas.py
 */

export interface SearchRequest {
  query: string
  collection_name?: string
  top_k?: number
  embedding_provider?: string | null
  rerank_provider?: string | null
  use_rerank?: boolean
}

export interface SearchResult {
  id: string
  text: string
  score: number
  metadata: Record<string, unknown>
  rerank_score?: number | null
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  total: number
  collection: string
  embedding_provider: string
  rerank_provider: string | null
}

export interface CollectionInfo {
  name: string
  count: number
  metadata: Record<string, unknown>
}

export interface CollectionsListResponse {
  collections: CollectionInfo[]
  total: number
}