import { describe, it, expect } from 'vitest'
import {
  ApiError,
  ErrorCode,
  isApiError,
  getErrorMessage,
} from '@/api/errors'
import type { AxiosError } from 'axios'

describe('ApiError', () => {
  describe('constructor', () => {
    it('should create ApiError with all parameters', () => {
      const error = new ApiError(
        'Test error',
        ErrorCode.INVALID_REQUEST,
        400,
        { field: 'name' }
      )

      expect(error.message).toBe('Test error')
      expect(error.code).toBe(ErrorCode.INVALID_REQUEST)
      expect(error.status).toBe(400)
      expect(error.detail).toEqual({ field: 'name' })
      expect(error.name).toBe('ApiError')
    })

    it('should create ApiError with default values', () => {
      const error = new ApiError('Test error')

      expect(error.code).toBe(ErrorCode.UNKNOWN_ERROR)
      expect(error.status).toBe(500)
      expect(error.detail).toBeNull()
    })
  })

  describe('fromAxiosError', () => {
    it('should create timeout error when request times out', () => {
      const axiosError = {
        response: undefined,
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
      } as AxiosError

      const error = ApiError.fromAxiosError(axiosError)

      expect(error.code).toBe(ErrorCode.TIMEOUT_ERROR)
      expect(error.status).toBe(0)
      expect(error.message).toBe('Request timed out')
    })

    it('should create network error when no response', () => {
      const axiosError = {
        response: undefined,
        code: 'ERR_NETWORK',
        message: 'Network Error',
      } as AxiosError

      const error = ApiError.fromAxiosError(axiosError)

      expect(error.code).toBe(ErrorCode.NETWORK_ERROR)
      expect(error.status).toBe(0)
      expect(error.message).toBe('Network error - please check your connection')
    })

    it('should map 400 status to INVALID_REQUEST', () => {
      const axiosError = {
        response: {
          status: 400,
          data: { message: 'Bad request' },
        },
      } as AxiosError

      const error = ApiError.fromAxiosError(axiosError)

      expect(error.code).toBe(ErrorCode.INVALID_REQUEST)
      expect(error.status).toBe(400)
    })

    it('should map 404 status to COLLECTION_NOT_FOUND', () => {
      const axiosError = {
        response: {
          status: 404,
          data: { message: 'Not found' },
        },
      } as AxiosError

      const error = ApiError.fromAxiosError(axiosError)

      expect(error.code).toBe(ErrorCode.COLLECTION_NOT_FOUND)
      expect(error.status).toBe(404)
    })

    it('should map 503 status to SERVICE_UNAVAILABLE', () => {
      const axiosError = {
        response: {
          status: 503,
          data: { message: 'Service unavailable' },
        },
      } as AxiosError

      const error = ApiError.fromAxiosError(axiosError)

      expect(error.code).toBe(ErrorCode.SERVICE_UNAVAILABLE)
      expect(error.status).toBe(503)
    })

    it('should use error code from response data', () => {
      const axiosError = {
        response: {
          status: 500,
          data: {
            error: ErrorCode.SEARCH_FAILED,
            message: 'Search failed',
          },
        },
      } as AxiosError

      const error = ApiError.fromAxiosError(axiosError)

      expect(error.code).toBe(ErrorCode.SEARCH_FAILED)
    })
  })

  describe('is method', () => {
    it('should return true when code matches', () => {
      const error = new ApiError('Test', ErrorCode.COLLECTION_NOT_FOUND)

      expect(error.is(ErrorCode.COLLECTION_NOT_FOUND)).toBe(true)
      expect(error.is(ErrorCode.INVALID_REQUEST)).toBe(false)
    })
  })

  describe('isNetworkError', () => {
    it('should return true for network and timeout errors', () => {
      const networkError = new ApiError('Network', ErrorCode.NETWORK_ERROR)
      const timeoutError = new ApiError('Timeout', ErrorCode.TIMEOUT_ERROR)
      const otherError = new ApiError('Other', ErrorCode.INVALID_REQUEST)

      expect(networkError.isNetworkError()).toBe(true)
      expect(timeoutError.isNetworkError()).toBe(true)
      expect(otherError.isNetworkError()).toBe(false)
    })
  })

  describe('isNotFoundError', () => {
    it('should return true for not found errors', () => {
      const collectionNotFound = new ApiError('Test', ErrorCode.COLLECTION_NOT_FOUND)
      const documentNotFound = new ApiError('Test', ErrorCode.DOCUMENT_NOT_FOUND)
      const taskNotFound = new ApiError('Test', ErrorCode.TASK_NOT_FOUND)
      const providerNotFound = new ApiError('Test', ErrorCode.PROVIDER_NOT_FOUND)
      const otherError = new ApiError('Test', ErrorCode.INVALID_REQUEST)

      expect(collectionNotFound.isNotFoundError()).toBe(true)
      expect(documentNotFound.isNotFoundError()).toBe(true)
      expect(taskNotFound.isNotFoundError()).toBe(true)
      expect(providerNotFound.isNotFoundError()).toBe(true)
      expect(otherError.isNotFoundError()).toBe(false)
    })
  })

  describe('getUserMessage', () => {
    it('should return localized message for network error', () => {
      const error = new ApiError('Network', ErrorCode.NETWORK_ERROR)
      expect(error.getUserMessage()).toBe('网络连接失败，请检查网络后重试')
    })

    it('should return localized message for timeout error', () => {
      const error = new ApiError('Timeout', ErrorCode.TIMEOUT_ERROR)
      expect(error.getUserMessage()).toBe('请求超时，请稍后重试')
    })

    it('should return localized message for collection not found', () => {
      const error = new ApiError('Not found', ErrorCode.COLLECTION_NOT_FOUND)
      expect(error.getUserMessage()).toBe('集合不存在')
    })

    it('should return original message for unknown error', () => {
      const error = new ApiError('Custom error message', ErrorCode.UNKNOWN_ERROR)
      expect(error.getUserMessage()).toBe('Custom error message')
    })
  })
})

describe('isApiError', () => {
  it('should return true for ApiError instances', () => {
    const error = new ApiError('Test')
    expect(isApiError(error)).toBe(true)
  })

  it('should return false for regular Error', () => {
    const error = new Error('Test')
    expect(isApiError(error)).toBe(false)
  })

  it('should return false for non-error values', () => {
    expect(isApiError('error string')).toBe(false)
    expect(isApiError(null)).toBe(false)
    expect(isApiError(undefined)).toBe(false)
  })
})

describe('getErrorMessage', () => {
  it('should return user message for ApiError', () => {
    const error = new ApiError('Test', ErrorCode.NETWORK_ERROR)
    expect(getErrorMessage(error)).toBe('网络连接失败，请检查网络后重试')
  })

  it('should return message for regular Error', () => {
    const error = new Error('Regular error')
    expect(getErrorMessage(error)).toBe('Regular error')
  })

  it('should return default message for non-error', () => {
    expect(getErrorMessage('string')).toBe('操作失败，请重试')
    expect(getErrorMessage(null)).toBe('操作失败，请重试')
  })
})
