import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { ApiError } from './errors'
import type { ErrorResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - convert Axios errors to ApiError
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<ErrorResponse>) => {
    // Convert to ApiError for unified error handling
    const apiError = ApiError.fromAxiosError(error)
    console.error(`API Error [${apiError.code}]: ${apiError.message}`)
    return Promise.reject(apiError)
  }
)

export default apiClient