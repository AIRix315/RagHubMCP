import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiError, ErrorCode } from '@/api/errors'
import type { IndexRequest, IndexResponse, IndexTaskStatus } from '@/types'

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
import { startIndex, getIndexStatus, listIndexTasks } from '@/api/indexing'

describe('api/indexing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('startIndex', () => {
    const mockRequest: IndexRequest = {
      path: '/path/to/code',
      collection_name: 'my-collection',
      embedding_provider: 'openai',
      chunk_size: 500,
      chunk_overlap: 50,
      recursive: true,
    }

    const mockResponse: IndexResponse = {
      task_id: 'task-123-456',
      message: 'Indexing started successfully',
      status_url: '/index/status/task-123-456',
    }

    it('should call POST /index with correct request', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      await startIndex(mockRequest)

      expect(apiClient.post).toHaveBeenCalledWith('/index', mockRequest)
      expect(apiClient.post).toHaveBeenCalledTimes(1)
    })

    it('should return IndexResponse on success', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await startIndex(mockRequest)

      expect(result).toEqual(mockResponse)
      expect(result.task_id).toBe('task-123-456')
      expect(result.message).toBe('Indexing started successfully')
    })

    it('should return status_url for tracking', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await startIndex(mockRequest)

      expect(result.status_url).toBe('/index/status/task-123-456')
    })

    it('should handle minimal request with only path', async () => {
      const minimalRequest: IndexRequest = {
        path: '/minimal/path',
      }
      const minimalResponse: IndexResponse = {
        task_id: 'task-minimal',
        message: 'Indexing started',
        status_url: '/index/status/task-minimal',
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: minimalResponse })

      const result = await startIndex(minimalRequest)

      expect(apiClient.post).toHaveBeenCalledWith('/index', minimalRequest)
      expect(result.task_id).toBe('task-minimal')
    })

    it('should handle request with null optional values', async () => {
      const requestWithNulls: IndexRequest = {
        path: '/path',
        embedding_provider: null,
        chunk_size: null,
        chunk_overlap: null,
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse })

      await startIndex(requestWithNulls)

      expect(apiClient.post).toHaveBeenCalledWith('/index', requestWithNulls)
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.post).mockRejectedValue(networkError)

      await expect(startIndex(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should throw ApiError on 400 Invalid Request', async () => {
      const invalidError = new ApiError(
        'Invalid path',
        ErrorCode.INVALID_REQUEST,
        400
      )
      vi.mocked(apiClient.post).mockRejectedValue(invalidError)

      await expect(startIndex(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.INVALID_REQUEST,
        status: 400,
      })
    })

    it('should throw ApiError on 503 Service Unavailable', async () => {
      const serviceError = new ApiError(
        'Embedding provider unavailable',
        ErrorCode.PROVIDER_UNAVAILABLE,
        503
      )
      vi.mocked(apiClient.post).mockRejectedValue(serviceError)

      await expect(startIndex(mockRequest)).rejects.toMatchObject({
        code: ErrorCode.PROVIDER_UNAVAILABLE,
      })
    })
  })

  describe('getIndexStatus', () => {
    const mockTaskStatus: IndexTaskStatus = {
      task_id: 'task-123-456',
      status: 'running',
      progress: 50,
      message: 'Processing files...',
      total_files: 100,
      processed_files: 50,
      total_chunks: 500,
      created_at: '2024-01-15T10:00:00Z',
      completed_at: null,
      error: null,
    }

    it('should call GET /index/status/:taskId', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockTaskStatus })

      await getIndexStatus('task-123-456')

      expect(apiClient.get).toHaveBeenCalledWith('/index/status/task-123-456')
      expect(apiClient.get).toHaveBeenCalledTimes(1)
    })

    it('should return IndexTaskStatus on success', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockTaskStatus })

      const result = await getIndexStatus('task-123-456')

      expect(result).toEqual(mockTaskStatus)
      expect(result.task_id).toBe('task-123-456')
      expect(result.status).toBe('running')
    })

    it('should return progress information', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockTaskStatus })

      const result = await getIndexStatus('task-123-456')

      expect(result.progress).toBe(50)
      expect(result.total_files).toBe(100)
      expect(result.processed_files).toBe(50)
      expect(result.total_chunks).toBe(500)
    })

    it('should handle completed task status', async () => {
      const completedStatus: IndexTaskStatus = {
        task_id: 'task-completed',
        status: 'completed',
        progress: 100,
        message: 'Indexing completed',
        total_files: 100,
        processed_files: 100,
        total_chunks: 1000,
        created_at: '2024-01-15T10:00:00Z',
        completed_at: '2024-01-15T10:30:00Z',
        error: null,
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: completedStatus })

      const result = await getIndexStatus('task-completed')

      expect(result.status).toBe('completed')
      expect(result.progress).toBe(100)
      expect(result.completed_at).toBe('2024-01-15T10:30:00Z')
    })

    it('should handle failed task status with error', async () => {
      const failedStatus: IndexTaskStatus = {
        task_id: 'task-failed',
        status: 'failed',
        progress: 30,
        message: 'Indexing failed',
        total_files: 100,
        processed_files: 30,
        total_chunks: 150,
        created_at: '2024-01-15T10:00:00Z',
        completed_at: '2024-01-15T10:10:00Z',
        error: 'Embedding provider error: API rate limit exceeded',
      }

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: failedStatus })

      const result = await getIndexStatus('task-failed')

      expect(result.status).toBe('failed')
      expect(result.error).toBe('Embedding provider error: API rate limit exceeded')
    })

    it('should throw ApiError on 404 Task Not Found', async () => {
      const notFoundError = new ApiError(
        'Task not found',
        ErrorCode.TASK_NOT_FOUND,
        404
      )
      vi.mocked(apiClient.get).mockRejectedValue(notFoundError)

      await expect(getIndexStatus('nonexistent-task')).rejects.toMatchObject({
        code: ErrorCode.TASK_NOT_FOUND,
        status: 404,
      })
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.get).mockRejectedValue(networkError)

      await expect(getIndexStatus('task-123')).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })
  })

  describe('listIndexTasks', () => {
    const mockTasks: IndexTaskStatus[] = [
      {
        task_id: 'task-1',
        status: 'completed',
        progress: 100,
        message: 'Done',
        total_files: 50,
        processed_files: 50,
        total_chunks: 500,
        created_at: '2024-01-15T09:00:00Z',
        completed_at: '2024-01-15T09:30:00Z',
        error: null,
      },
      {
        task_id: 'task-2',
        status: 'running',
        progress: 25,
        message: 'Processing...',
        total_files: 200,
        processed_files: 50,
        total_chunks: 200,
        created_at: '2024-01-15T10:00:00Z',
        completed_at: null,
        error: null,
      },
    ]

    it('should call GET /index/status', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockTasks })

      await listIndexTasks()

      expect(apiClient.get).toHaveBeenCalledWith('/index/status')
      expect(apiClient.get).toHaveBeenCalledTimes(1)
    })

    it('should return array of IndexTaskStatus', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockTasks })

      const result = await listIndexTasks()

      expect(result).toEqual(mockTasks)
      expect(result).toHaveLength(2)
    })

    it('should return empty array when no tasks', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [] })

      const result = await listIndexTasks()

      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })

    it('should include all task statuses', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockTasks })

      const result = await listIndexTasks()

      expect(result[0].status).toBe('completed')
      expect(result[1].status).toBe('running')
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.get).mockRejectedValue(networkError)

      await expect(listIndexTasks()).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should throw ApiError on 503 Service Unavailable', async () => {
      const serviceError = new ApiError(
        'Service unavailable',
        ErrorCode.SERVICE_UNAVAILABLE,
        503
      )
      vi.mocked(apiClient.get).mockRejectedValue(serviceError)

      await expect(listIndexTasks()).rejects.toMatchObject({
        code: ErrorCode.SERVICE_UNAVAILABLE,
      })
    })
  })
})