import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiError, ErrorCode } from '@/api/errors'
import type { ConfigModel, ConfigUpdateRequest, SuccessResponse } from '@/types'

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
import { getConfig, updateConfig } from '@/api/config'

describe('api/config', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getConfig', () => {
    const mockConfig: ConfigModel = {
      server: {
        host: '0.0.0.0',
        port: 8818,
        debug: true,
      },
      chroma: {
        persist_dir: './data/chroma',
        host: null,
        port: null,
      },
      providers: {
        embedding: {
          default: 'openai',
          instances: [
            { name: 'openai', type: 'openai', model: 'text-embedding-3-small' },
          ],
        },
        rerank: {
          default: 'flashrank',
          instances: [
            { name: 'flashrank', type: 'flashrank', model: 'default' },
          ],
        },
        llm: {
          default: 'openai',
          instances: [
            { name: 'openai', type: 'openai', model: 'gpt-4' },
          ],
        },
      },
      indexer: {
        chunk_size: 500,
        chunk_overlap: 50,
        max_file_size: 10485760,
        file_types: ['.py', '.js', '.ts'],
        exclude_dirs: ['node_modules', '.git'],
      },
      logging: {
        level: 'INFO',
        format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        file: null,
      },
      hybrid: null,
      watcher: null,
    }

    it('should call GET /config', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig })

      await getConfig()

      expect(apiClient.get).toHaveBeenCalledWith('/config')
      expect(apiClient.get).toHaveBeenCalledTimes(1)
    })

    it('should return ConfigModel on success', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig })

      const result = await getConfig()

      expect(result).toEqual(mockConfig)
      expect(result.server.host).toBe('0.0.0.0')
      expect(result.server.port).toBe(8818)
    })

    it('should return providers configuration', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig })

      const result = await getConfig()

      expect(result.providers.embedding.default).toBe('openai')
      expect(result.providers.rerank.default).toBe('flashrank')
      expect(result.providers.llm.default).toBe('openai')
    })

    it('should return indexer configuration', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig })

      const result = await getConfig()

      expect(result.indexer.chunk_size).toBe(500)
      expect(result.indexer.chunk_overlap).toBe(50)
      expect(result.indexer.file_types).toContain('.py')
      expect(result.indexer.exclude_dirs).toContain('node_modules')
    })

    it('should throw ApiError on network error', async () => {
      const networkError = new ApiError(
        'Network error - please check your connection',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.get).mockRejectedValue(networkError)

      await expect(getConfig()).rejects.toMatchObject({
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

      await expect(getConfig()).rejects.toMatchObject({
        code: ErrorCode.SERVICE_UNAVAILABLE,
        status: 503,
      })
    })
  })

  describe('updateConfig', () => {
    const mockSuccessResponse: SuccessResponse = {
      status: 'success',
      message: 'Configuration updated successfully',
    }

    it('should call PUT /config with update data', async () => {
      const updateData: ConfigUpdateRequest = {
        server: {
          host: '127.0.0.1',
          port: 9000,
          debug: false,
        },
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockSuccessResponse })

      await updateConfig(updateData)

      expect(apiClient.put).toHaveBeenCalledWith('/config', updateData)
      expect(apiClient.put).toHaveBeenCalledTimes(1)
    })

    it('should return SuccessResponse on successful update', async () => {
      const updateData: ConfigUpdateRequest = {
        logging: {
          level: 'DEBUG',
          format: '%(message)s',
          file: '/var/log/raghub.log',
        },
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockSuccessResponse })

      const result = await updateConfig(updateData)

      expect(result).toEqual(mockSuccessResponse)
      expect(result.status).toBe('success')
    })

    it('should update indexer configuration', async () => {
      const updateData: ConfigUpdateRequest = {
        indexer: {
          chunk_size: 1000,
          chunk_overlap: 100,
          max_file_size: 20971520,
          file_types: ['.py', '.js', '.ts', '.md'],
          exclude_dirs: ['node_modules', '.git', 'dist'],
        },
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockSuccessResponse })

      await updateConfig(updateData)

      expect(apiClient.put).toHaveBeenCalledWith('/config', updateData)
    })

    it('should update providers configuration', async () => {
      const updateData: ConfigUpdateRequest = {
        providers: {
          embedding: {
            default: 'ollama',
            instances: [
              { name: 'ollama', type: 'ollama', model: 'nomic-embed-text' },
            ],
          },
          rerank: {
            default: 'flashrank',
            instances: [
              { name: 'flashrank', type: 'flashrank', model: 'default' },
            ],
          },
          llm: {
            default: 'ollama',
            instances: [
              { name: 'ollama', type: 'ollama', model: 'llama2' },
            ],
          },
        },
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockSuccessResponse })

      await updateConfig(updateData)

      expect(apiClient.put).toHaveBeenCalledWith('/config', updateData)
    })

    it('should throw ApiError on 400 Invalid Config', async () => {
      const updateData: ConfigUpdateRequest = {
        server: {
          host: '',
          port: -1,
          debug: true,
        },
      }

      const invalidConfigError = new ApiError(
        'Invalid configuration',
        ErrorCode.INVALID_CONFIG,
        400
      )
      vi.mocked(apiClient.put).mockRejectedValue(invalidConfigError)

      await expect(updateConfig(updateData)).rejects.toMatchObject({
        code: ErrorCode.INVALID_CONFIG,
        status: 400,
      })
    })

    it('should throw ApiError on network error', async () => {
      const updateData: ConfigUpdateRequest = { server: undefined }
      const networkError = new ApiError(
        'Network error',
        ErrorCode.NETWORK_ERROR,
        0
      )
      vi.mocked(apiClient.put).mockRejectedValue(networkError)

      await expect(updateConfig(updateData)).rejects.toMatchObject({
        code: ErrorCode.NETWORK_ERROR,
      })
    })

    it('should handle partial config updates', async () => {
      const partialUpdate: ConfigUpdateRequest = {
        indexer: {
          chunk_size: 800,
          chunk_overlap: 80,
          max_file_size: 10485760,
          file_types: ['.py'],
          exclude_dirs: [],
        },
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockSuccessResponse })

      const result = await updateConfig(partialUpdate)

      expect(result.status).toBe('success')
    })

    it('should handle null values for optional configs', async () => {
      const updateWithNulls: ConfigUpdateRequest = {
        hybrid: null,
        watcher: null,
      }

      vi.mocked(apiClient.put).mockResolvedValueOnce({ data: mockSuccessResponse })

      await updateConfig(updateWithNulls)

      expect(apiClient.put).toHaveBeenCalledWith('/config', updateWithNulls)
    })
  })
})