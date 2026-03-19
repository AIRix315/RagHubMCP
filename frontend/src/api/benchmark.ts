import apiClient from './client'
import type { BenchmarkRequest, BenchmarkResponse } from '@/types'

/**
 * Run a benchmark comparison
 * TC-1.15.6: POST /api/benchmark executes comparison
 */
export async function runBenchmark(request: BenchmarkRequest): Promise<BenchmarkResponse> {
  const response = await apiClient.post<BenchmarkResponse>('/benchmark', request)
  return response.data
}