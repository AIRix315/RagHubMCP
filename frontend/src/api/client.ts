import axios, { type AxiosInstance, type AxiosError } from 'axios'
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

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<ErrorResponse>) => {
    if (error.response?.data) {
      const errorData = error.response.data
      console.error(`API Error: ${errorData.error} - ${errorData.message}`)
    }
    return Promise.reject(error)
  }
)

export default apiClient