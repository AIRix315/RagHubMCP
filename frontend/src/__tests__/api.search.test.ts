import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiError, ErrorCode } from '@/api/errors'
import type { SearchRequest, SearchResponse, CollectionsListResponse } from '@/types'

// Mock the apiClient module
vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

// Import after mocking
import apiClient from '@/api/client'
import { executeSearch, listCollections, deleteCollection } from '@/api/search'

describe('api/search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('executeSearch', () => {
    const mockRequest: SearchRequest = {
      query: 'how to implement authentication',
      collection_name: 'code-docs',
      top_k: 10,
      embedding_provider: 'openai',
      rerank_provider: 'flashrank',
      use_rerank: true,
    }

    const mockResponse: SearchResponse = {
      query: 'how to implement authentication',
      results: [
        {
          id: 'doc-1',
          text: 'Authentication can be implemented using JWT tokens...',
          score: 0.95,
          metadata: { source: 'auth.py', line: 10 },
          rerank_score: 0.92,
        },
        {
          id: 'doc-2',
          text: 'OAuth2 is a popular authentication protocol...',
          score: 0.88,
          metadata: { source: 'oauth.py', line: 5 },
          rerank_score: 0.85,
        },
      ],
      total: 2,
      collection: 'code-docs',
      embedding_provider: 'openai',
      rerank_provider: 'flashrank',
    }

    it('should call POST /search with correct request', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      await executeSearch(mockRequest)

      expect(apiClient.post).toHaveBeenCalledWith('/search', mockRequest)
      expect(apiClient.post).toHaveBeenCalledTimes(1)
    })

    it('should return SearchResponse on success', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await executeSearch(mockRequest)

      expect(result).toEqual(mockResponse)
      expect(result.query).toBe('how to implement authentication')
      expect(result.total).toBe(2)
    })

    it('should return search results with scores', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await executeSearch(mockRequest)

      expect(result.results).toHaveLength(2)
      expect(result.results[0].score).toBe(0.95)
      expect(result.results[0].rerank_score).toBe(0.92)
    })

    it('should return collection and provider info', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await executeSearch(mockRequest)

      expect(result.collection).toBe('code-docs')
      expect(result.embedding_provider).toBe('openai')
      expect(result.rerank_provider).toBe('flashrank')
    })

    it('should handle search without rerank', async () => {
      const noRerankRequest: SearchRequest = {
        query: 'test query',
        use_rerank: false,
      }
      const noRerankResponse: SearchResponse = {
        query: 'test query',
        results: [
          {
            id: 'doc-1',
            text: 'sample text',
            score: 0.9,
            metadata: {},
            rerank_score: null,
          },
        ],
        total: 1,
        collection: 'default',
        embedding_provider: 'default',
        rerank_provider: null,
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: noRerankResponse })

      const result = await executeSearch(noRerankRequest)

      expect(result.rerank_provider).toBeNull()
      expect(result.results[0].rerank_score).toBeNull()
    })

    it('should handle minimal search request', async () => {
      const minimalRequest: SearchRequest = {
        query: 'simple query',
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      await executeSearch(minimalRequest)

      expect(apiClient.post).toHaveBeenCalledWith('/search', minimalRequest)
    })

    it('should handle empty results', async () => {
      const emptyResponse: SearchResponse = {
        query: 'nonexistent',
        results: [],
        total: 0,
        collection: 'default',
        embedding_provider: 'openai',
        rerank_provider: null,
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: emptyResponse })

      const result = await executeSearch({ query: 'nonexistent' })

      expect(result.results).toHaveLength(0)
      expect(result.total).toBe(0)
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.post).mockRejectedValue(networkError)

      await expect(executeSearch(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should throw ApiError on 400 Invalid Query', async () => {
      const invalidError = new ApiError(
        'Invalid query',
        ErrorCode.INVALID_QUERY,
        400
      )
      vi.mocked(apiClient.post).mockRejectedValue(invalidError)

      await expect(executeSearch(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.INVALID_QUERY,
        status: 400,
      })
    })

    it('should throw ApiError on 404 Collection Not Found', async () => {
      const notFoundError = new ApiError(
        'Collection not found',
        ErrorCode.COLLECTION_NOT_FOUND,
        404
      )
      vi.mocked(apiClient.post).mockRejectedValue(notFoundError)

      await expect(executeSearch(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.COLLECTION_NOT_FOUND,
        status: 404,
      })
    })

    it('should throw ApiError on 500 Search Failed', async () => {
      const searchError = new ApiError(
        'Search failed',
        ErrorCode.SEARCH_FAILED,
        500
      )
      vi.mocked(apiClient.post).mockRejectedValue(searchError)

      await expect(executeSearch(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.SEARCH_FAILED,
        status: 500,
      })
    })
  })

  describe('listCollections', () => {
    const mockCollectionsResponse: CollectionsListResponse = {
      collections: [
        {
          name: 'code-docs',
          count: 1500,
          metadata: { created_at: '2024-01-01', source: 'github' },
        },
        {
          name: 'knowledge-base',
          count: 500,
          metadata: { created_at: '2024-01-15' },
        },
      ],
      total: 2,
    }

    it('should call GET /search/collections', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockCollectionsResponse })

      await listCollections()

      expect(apiClient.get).toHaveBeenCalledWith('/search/collections')
      expect(apiClient.get).toHaveBeenCalledTimes(1)
    })

    it('should return CollectionsListResponse on success', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockCollectionsResponse })

      const result = await listCollections()

      expect(result).toEqual(mockCollectionsResponse)
      expect(result.total).toBe(2)
    })

    it('should return collection info with counts', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockCollectionsResponse })

      const result = await listCollections()

      expect(result.collections[0].name).toBe('code-docs')
      expect(result.collections[0].count).toBe(1500)
      expect(result.collections[1].name).toBe('knowledge-base')
      expect(result.collections[1].count).toBe(500)
    })

    it('should return empty collections list', async () => {
      const emptyResponse: CollectionsListResponse = {
        collections: [],
        total: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: emptyResponse })

      const result = await listCollections()

      expect(result.collections).toHaveLength(0)
      expect(result.total).toBe(0)
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.get).mockRejectedValue(networkError)

      await expect(listCollections()).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should throw ApiError on 503 Service Unavailable', async () => {
      const serviceError = new ApiError(
        'Database error',
        ErrorCode.DATABASE_ERROR,
        503
      )
      vi.mocked(apiClient.get).mockRejectedValue(serviceError)

      await expect(listCollections()).rejects.toMatchObject({
        code: ErrorCode.DATABASE_ERROR,
      })
    })
  })

  describe('deleteCollection', () => {
    const mockDeleteResponse = {
      name: 'test-collection',
      message: 'Collection deleted successfully',
    }

    it('should call DELETE /search/collections/:name', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockDeleteResponse })

      await deleteCollection('test-collection')

      expect(apiClient.delete).toHaveBeenCalledWith('/search/collections/test-collection')
      expect(apiClient.delete).toHaveBeenCalledTimes(1)
    })

    it('should return delete confirmation', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: mockDeleteResponse })

      const result = await deleteCollection('test-collection')

      expect(result).toEqual(mockDeleteResponse)
      expect(result.name).toBe('test-collection')
      expect(result.message).toBe('Collection deleted successfully')
    })

    it('should handle collection name with special characters', async () => {
      const specialName = 'my-collection_2024'
      const response = {
        name: specialName,
        message: 'Collection deleted',
      }

      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: response })

      await deleteCollection(specialName)

      expect(apiClient.delete).toHaveBeenCalledWith(`/search/collections/${specialName}`)
    })

    it('should throw ApiError on 404 Collection Not Found', async () => {
      const notFoundError = new ApiError(
        'Collection not found',
        ErrorCode.COLLECTION_NOT_FOUND,
        404
      )
      vi.mocked(apiClient.delete).mockRejectedValue(notFoundError)

      await expect(deleteCollection('nonexistent')).rejects.toMatchObject({
        code: ErrorCode.COLLECTION_NOT_FOUND,
        status: 404,
      })
    })

    it('should throw ApiError on 400 Invalid Collection', async () => {
      const invalidError = new ApiError(
        'Invalid collection name',
        ErrorCode.INVALID_COLLECTION,
        400
      )
      vi.mocked(apiClient.delete).mockRejectedValue(invalidError)

      await expect(deleteCollection('')).rejects.toMatchObject({
        code: ErrorCode.INVALID_COLLECTION,
        status: 400,
      })
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.delete).mockRejectedValue(networkError)

      await expect(deleteCollection('test')).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should throw ApiError on 503 Database Error', async () => {
      const dbError = new ApiError(
        'Database error',
        ErrorCode.DATABASE_ERROR,
        503
      )
      vi.mocked(apiClient.delete).mockRejectedValue(dbError)

      await expect(deleteCollection('test')).rejects.toMatchObject({
        code: ErrorCode.DATABASE_ERROR,
      })
    })
  })
})