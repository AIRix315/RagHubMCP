import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ErrorCode } from '@/api/errors'

// Mock axios - vi.mock is hoisted, factory cannot reference external variables
// Define everything inside the factory and expose via module exports
vi.mock('axios', () => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return {
    __esModule: true,
    default: {
      create: vi.fn(() => mockInstance),
    },
    // Export mock instance for testing
    mockInstance,
  }
})

// Import the mocked module
import * as axiosModule from 'axios'

describe('apiClient', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    // Re-import client module to re-trigger interceptor registration after clearing mocks
    vi.resetModules()
    await import('@/api/client')
  })

  describe('axios instance creation', () => {
    it('should call axios.create', () => {
      expect((axiosModule.default as any).create).toHaveBeenCalled()
    })
  })

  describe('request interceptor', () => {
    it('should register request interceptor', () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      expect(mockInstance?.interceptors.request.use).toHaveBeenCalled()
    })
  })

  describe('response interceptor', () => {
    it('should register response interceptor', () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      expect(mockInstance?.interceptors.response.use).toHaveBeenCalled()
    })

    it('should convert timeout error to ApiError', async () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      const errorHandler = mockInstance?.interceptors.response.use.mock.calls[0]?.[1]
      
      if (errorHandler) {
        const timeoutError = {
          response: undefined,
          code: 'ECONNABORTED',
          message: 'timeout',
        }
        
        try {
          await errorHandler(timeoutError)
          expect.fail('Should have thrown')
        } catch (error) {
          // Check ApiError properties instead of instanceof to avoid module caching issues
          expect(error).toHaveProperty('code')
          expect((error as any).code).toBe(ErrorCode.TIMEOUT_ERROR)
        }
      }
    })

    it('should convert network error to ApiError', async () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      const errorHandler = mockInstance?.interceptors.response.use.mock.calls[0]?.[1]
      
      if (errorHandler) {
        const networkError = {
          response: undefined,
          code: 'ERR_NETWORK',
          message: 'Network Error',
        }
        
        try {
          await errorHandler(networkError)
          expect.fail('Should have thrown')
        } catch (error) {
          expect(error).toHaveProperty('code')
          expect((error as any).code).toBe(ErrorCode.NETWORK_ERROR)
        }
      }
    })

    it('should convert 400 response to INVALID_REQUEST', async () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      const errorHandler = mockInstance?.interceptors.response.use.mock.calls[0]?.[1]
      
      if (errorHandler) {
        const badRequestError = {
          response: {
            status: 400,
            data: { message: 'Bad request' },
          },
        }
        
        try {
          await errorHandler(badRequestError)
          expect.fail('Should have thrown')
        } catch (error) {
          expect(error).toHaveProperty('code')
          expect((error as any).code).toBe(ErrorCode.INVALID_REQUEST)
          expect((error as any).status).toBe(400)
        }
      }
    })

    it('should convert 404 response to COLLECTION_NOT_FOUND', async () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      const errorHandler = mockInstance?.interceptors.response.use.mock.calls[0]?.[1]
      
      if (errorHandler) {
        const notFoundError = {
          response: {
            status: 404,
            data: { message: 'Not found' },
          },
        }
        
        try {
          await errorHandler(notFoundError)
          expect.fail('Should have thrown')
        } catch (error) {
          expect(error).toHaveProperty('code')
          expect((error as any).code).toBe(ErrorCode.COLLECTION_NOT_FOUND)
          expect((error as any).status).toBe(404)
        }
      }
    })

    it('should convert 503 response to SERVICE_UNAVAILABLE', async () => {
      const mockInstance = (axiosModule.default as any).create.mock.results[0]?.value
      const errorHandler = mockInstance?.interceptors.response.use.mock.calls[0]?.[1]
      
      if (errorHandler) {
        const serviceError = {
          response: {
            status: 503,
            data: { message: 'Service unavailable' },
          },
        }
        
        try {
          await errorHandler(serviceError)
          expect.fail('Should have thrown')
        } catch (error) {
          expect(error).toHaveProperty('code')
          expect((error as any).code).toBe(ErrorCode.SERVICE_UNAVAILABLE)
          expect((error as any).status).toBe(503)
        }
      }
    })
  })
})
