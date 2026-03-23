/**
 * Collection types matching backend/src/api/schemas.py
 */

export interface CollectionInfo {
  name: string
  count: number
  metadata: Record<string, any>
}

export interface CollectionsListResponse {
  collections: CollectionInfo[]
  total: number
}

export interface CollectionDeleteResponse {
  name: string
  message: string
}

export interface CollectionDetail extends CollectionInfo {
  // Extended info for detail view
  created_at?: string
  updated_at?: string
  embedding_function?: string
  distance_function?: string
}

export interface CollectionDocument {
  id: string
  text: string
  metadata: Record<string, any>
  embedding?: number[]
}

export interface CollectionDocumentsResponse {
  documents: CollectionDocument[]
  total: number
  page: number
  page_size: number
}
