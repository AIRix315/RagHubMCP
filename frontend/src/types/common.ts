/**
 * Common response types matching backend/src/api/schemas.py
 */

export interface ErrorResponse {
  error: string
  message: string
  detail?: Record<string, unknown> | null
}

export interface SuccessResponse {
  status: string
  message: string
}