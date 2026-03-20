/**
 * API Error handling utilities.
 * 
 * Provides unified error handling across the frontend:
 * - ApiError class for structured error information
 * - Error handling in API client
 * - Type-safe error handling in stores
 */

import type { AxiosError } from 'axios'

/**
 * Standard error codes matching backend ErrorCode enum
 */
export enum ErrorCode {
  // Validation errors (400)
  INVALID_REQUEST = 'invalid_request',
  INVALID_COLLECTION = 'invalid_collection',
  INVALID_QUERY = 'invalid_query',
  INVALID_CONFIG = 'invalid_config',
  
  // Not found errors (404)
  COLLECTION_NOT_FOUND = 'collection_not_found',
  DOCUMENT_NOT_FOUND = 'document_not_found',
  TASK_NOT_FOUND = 'task_not_found',
  PROVIDER_NOT_FOUND = 'provider_not_found',
  
  // Operation errors (500)
  SEARCH_FAILED = 'search_failed',
  INDEX_FAILED = 'index_failed',
  EMBEDDING_FAILED = 'embedding_failed',
  RERANK_FAILED = 'rerank_failed',
  PIPELINE_ERROR = 'pipeline_error',
  
  // Service errors (503)
  SERVICE_UNAVAILABLE = 'service_unavailable',
  PROVIDER_UNAVAILABLE = 'provider_unavailable',
  DATABASE_ERROR = 'database_error',
  
  // Client errors
  NETWORK_ERROR = 'network_error',
  TIMEOUT_ERROR = 'timeout_error',
  UNKNOWN_ERROR = 'unknown_error',
}

/**
 * API Error class for structured error handling.
 */
export class ApiError extends Error {
  public readonly code: ErrorCode
  public readonly status: number
  public readonly detail: Record<string, unknown> | null

  constructor(
    message: string,
    code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    status: number = 500,
    detail: Record<string, unknown> | null = null
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.detail = detail
  }

  /**
   * Create ApiError from Axios error response
   */
  static fromAxiosError(error: AxiosError<ErrorResponse>): ApiError {
    const response = error.response
    
    if (!response) {
      // Network error or timeout
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        return new ApiError(
          'Request timed out',
          ErrorCode.TIMEOUT_ERROR,
          0,
          null
        )
      }
      return new ApiError(
        'Network error - please check your connection',
        ErrorCode.NETWORK_ERROR,
        0,
        null
      )
    }

    const errorData = response.data
    const status = response.status

    // Map status to error code
    let code: ErrorCode
    if (status === 400) {
      code = ErrorCode.INVALID_REQUEST
    } else if (status === 404) {
      code = ErrorCode.COLLECTION_NOT_FOUND
    } else if (status === 503) {
      code = ErrorCode.SERVICE_UNAVAILABLE
    } else {
      code = ErrorCode.UNKNOWN_ERROR
    }

    return new ApiError(
      errorData?.message || `Request failed with status ${status}`,
      (errorData?.error as ErrorCode) || code,
      status,
      errorData?.detail || null
    )
  }

  /**
   * Check if error is a specific error code
   */
  is(code: ErrorCode): boolean {
    return this.code === code
  }

  /**
   * Check if error is a network error
   */
  isNetworkError(): boolean {
    return this.code === ErrorCode.NETWORK_ERROR || this.code === ErrorCode.TIMEOUT_ERROR
  }

  /**
   * Check if error is a not found error
   */
  isNotFoundError(): boolean {
    return [
      ErrorCode.COLLECTION_NOT_FOUND,
      ErrorCode.DOCUMENT_NOT_FOUND,
      ErrorCode.TASK_NOT_FOUND,
      ErrorCode.PROVIDER_NOT_FOUND,
    ].includes(this.code)
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    switch (this.code) {
      case ErrorCode.NETWORK_ERROR:
        return '网络连接失败，请检查网络后重试'
      case ErrorCode.TIMEOUT_ERROR:
        return '请求超时，请稍后重试'
      case ErrorCode.COLLECTION_NOT_FOUND:
        return '集合不存在'
      case ErrorCode.INVALID_REQUEST:
        return '请求参数无效'
      case ErrorCode.SERVICE_UNAVAILABLE:
        return '服务暂时不可用，请稍后重试'
      default:
        return this.message || '操作失败，请重试'
    }
  }
}

/**
 * Error response type from backend
 */
interface ErrorResponse {
  error?: string
  message?: string
  detail?: Record<string, unknown> | null
}

/**
 * Check if error is an ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

/**
 * Extract error message from unknown error
 */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.getUserMessage()
  }
  if (error instanceof Error) {
    return error.message
  }
  return '操作失败，请重试'
}