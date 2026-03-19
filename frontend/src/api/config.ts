import apiClient from './client'
import type { ConfigModel, ConfigUpdateRequest, SuccessResponse } from '@/types'

/**
 * Get current configuration
 * TC-1.15.1: GET /api/config returns configuration
 */
export async function getConfig(): Promise<ConfigModel> {
  const response = await apiClient.get<ConfigModel>('/config')
  return response.data
}

/**
 * Update configuration
 * TC-1.15.2: PUT /api/config updates configuration
 */
export async function updateConfig(data: ConfigUpdateRequest): Promise<SuccessResponse> {
  const response = await apiClient.put<SuccessResponse>('/config', data)
  return response.data
}