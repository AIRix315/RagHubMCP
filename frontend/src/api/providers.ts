import apiClient from './client'
import type {
  ProvidersListResponse,
  ProviderInfo,
  ProviderCreateRequest,
  ProviderUpdateResponse,
  ProviderDeleteResponse,
  SetDefaultProviderResponse,
  RerankTestRequest,
  RerankTestResponse,
  RerankCompareRequest,
  RerankCompareResponse,
  ProviderType,
} from '@/types'

/**
 * List all providers grouped by category
 * GET /api/providers
 */
export async function listProviders(): Promise<ProvidersListResponse> {
  const response = await apiClient.get<ProvidersListResponse>('/providers')
  return response.data
}

/**
 * List providers by type
 * GET /api/providers/{type}
 */
export async function listProvidersByType(type: ProviderType): Promise<ProviderInfo[]> {
  const response = await apiClient.get<ProviderInfo[]>(`/providers/${type}`)
  return response.data
}

/**
 * Get provider details
 * GET /api/providers/{type}/{name}
 */
export async function getProvider(type: ProviderType, name: string): Promise<ProviderInfo> {
  const response = await apiClient.get<ProviderInfo>(`/providers/${type}/${name}`)
  return response.data
}

/**
 * Create or update provider
 * PUT /api/providers/{type}/{name}
 */
export async function createOrUpdateProvider(
  type: ProviderType,
  name: string,
  data: ProviderCreateRequest
): Promise<ProviderUpdateResponse> {
  const response = await apiClient.put<ProviderUpdateResponse>(
    `/providers/${type}/${name}`,
    data
  )
  return response.data
}

/**
 * Delete provider
 * DELETE /api/providers/{type}/{name}
 */
export async function deleteProvider(
  type: ProviderType,
  name: string
): Promise<ProviderDeleteResponse> {
  const response = await apiClient.delete<ProviderDeleteResponse>(
    `/providers/${type}/${name}`
  )
  return response.data
}

/**
 * Set provider as default
 * POST /api/providers/{type}/{name}/set-default
 */
export async function setDefaultProvider(
  type: ProviderType,
  name: string
): Promise<SetDefaultProviderResponse> {
  const response = await apiClient.post<SetDefaultProviderResponse>(
    `/providers/${type}/${name}/set-default`
  )
  return response.data
}

/**
 * Test rerank provider
 * POST /api/providers/rerank/{name}/test
 */
export async function testRerankProvider(
  name: string,
  data: RerankTestRequest
): Promise<RerankTestResponse> {
  const response = await apiClient.post<RerankTestResponse>(
    `/providers/rerank/${name}/test`,
    data
  )
  return response.data
}

/**
 * Compare multiple rerank engines
 * POST /api/providers/rerank/compare
 */
export async function compareRerankEngines(
  data: RerankCompareRequest
): Promise<RerankCompareResponse> {
  const response = await apiClient.post<RerankCompareResponse>(
    '/providers/rerank/compare',
    data
  )
  return response.data
}
