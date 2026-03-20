import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiError, ErrorCode } from '@/api/errors'
import type { BenchmarkRequest, BenchmarkResponse } from '@/types'

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
import { runBenchmark } from '@/api/benchmark'

describe('api/benchmark', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('runBenchmark', () => {
    const mockRequest: BenchmarkRequest = {
      query: 'test query',
      collection_name: 'test-collection',
      configs: [
        {
          name: 'config1',
          embedding_provider: 'openai',
          rerank_provider: 'flashrank',
          top_k: 10,
        },
      ],
    }

    const mockResponse: BenchmarkResponse = {
      query: 'test query',
      collection: 'test-collection',
      results: [
        {
          config_name: 'config1',
          results: [
            {
              id: 'doc1',
              text: 'sample text',
              score: 0.95,
              metadata: { source: 'test' },
              rerank_score: 0.92,
            },
          ],
          latency_ms: 150,
          embedding_provider: 'openai',
          rerank_provider: 'flashrank',
        },
      ],
      total_latency_ms: 200,
    }

    it('should call POST /benchmark with correct request', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      await runBenchmark(mockRequest)

      expect(apiClient.post).toHaveBeenCalledWith('/benchmark', mockRequest)
      expect(apiClient.post).toHaveBeenCalledTimes(1)
    })

    it('should return benchmark response on success', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await runBenchmark(mockRequest)

      expect(result).toEqual(mockResponse)
      expect(result.query).toBe('test query')
      expect(result.collection).toBe('test-collection')
      expect(result.results).toHaveLength(1)
    })

    it('should return results with correct latency metrics', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await runBenchmark(mockRequest)

      expect(result.total_latency_ms).toBe(200)
      expect(result.results[0].latency_ms).toBe(150)
    })

    it('should handle multiple benchmark configs', async () => {
      const multiConfigRequest: BenchmarkRequest = {
        query: 'test query',
        configs: [
          { name: 'config1', embedding_provider: 'openai' },
          { name: 'config2', embedding_provider: 'ollama', rerank_provider: null },
        ],
      }
      const multiConfigResponse: BenchmarkResponse = {
        query: 'test query',
        collection: 'default',
        results: [
          {
            config_name: 'config1',
            results: [],
            latency_ms: 100,
            embedding_provider: 'openai',
            rerank_provider: null,
          },
          {
            config_name: 'config2',
            results: [],
            latency_ms: 120,
            embedding_provider: 'ollama',
            rerank_provider: null,
          },
        ],
        total_latency_ms: 220,
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: multiConfigResponse })

      const result = await runBenchmark(multiConfigRequest)

      expect(result.results).toHaveLength(2)
      expect(result.results[0].config_name).toBe('config1')
      expect(result.results[1].config_name).toBe('config2')
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error - please check your connection',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.post).mockRejectedValue(networkError)

      await expect(runBenchmark(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should throw ApiError on timeout error', async () => {
      const timeoutError = new ApiError(
        'Request timed out',
        ErrorCode.TIMEOUT_ERROR,
        0
      )
      vi.mocked(apiClient.post).mockRejectedValue(timeoutError)

      await expect(runBenchmark(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.TIMEOUT_ERROR,
      })
    })

    it('should throw ApiError on 400 Bad Request', async () => {
      const badRequestError = new ApiError(
        'Invalid benchmark config',
        ErrorCode.INVALID_REQUEST,
        400
      )
      vi.mocked(apiClient.post).mockRejectedValue(badRequestError)

      await expect(runBenchmark(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.INVALID_REQUEST,
        status: 400,
      })
    })

    it('should throw ApiError on 503 Service Unavailable', async () => {
      const serviceError = new ApiError(
        'Service unavailable',
        ErrorCode.SERVICE_UNAVAILABLE,
        503
      )
      vi.mocked(apiClient.post).mockRejectedValue(serviceError)

      await expect(runBenchmark(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.SERVICE_UNAVAILABLE,
        status: 503,
      })
    })

    it('should handle request without optional collection_name', async () => {
      const requestWithoutCollection: BenchmarkRequest = {
        query: 'test query',
        configs: [{ name: 'config1', embedding_provider: 'openai' }],
      }
      const response: BenchmarkResponse = {
        query: 'test query',
        collection: 'default',
        results: [],
        total_latency_ms: 100,
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: response })

      const result = await runBenchmark(requestWithoutCollection)

      expect(result.collection).toBe('default')
    })

    it('should handle empty configs array gracefully', async () => {
      const emptyConfigRequest: BenchmarkRequest = {
        query: 'test query',
        configs: [],
      }
      const emptyConfigResponse: BenchmarkResponse = {
        query: 'test query',
        collection: 'default',
        results: [],
        total_latency_ms: 10,
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: emptyConfigResponse })

      const result = await runBenchmark(emptyConfigRequest)

      expect(result.results).toHaveLength(0)
      expect(result.total_latency_ms).toBe(10)
    })

    it('should pass rerank_provider as null when not specified', async () => {
      const requestWithNullRerank: BenchmarkRequest = {
        query: 'test query',
        configs: [
          {
            name: 'config-no-rerank',
            embedding_provider: 'openai',
            rerank_provider: null,
          },
        ],
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      await runBenchmark(requestWithNullRerank)

      expect(apiClient.post).toHaveBeenCalledWith('/benchmark', requestWithNullRerank)
    })
  })
})