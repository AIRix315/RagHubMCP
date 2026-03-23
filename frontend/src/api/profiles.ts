/**
 * Profiles API
 * 
 * 根据 Docs/23-UI-Plan.md 定义
 * 用于配置预设管理
 */

import apiClient from './client'
import type { PipelineConfig, PipelineUpdateResponse } from '@/types/pipeline'
import type { ProfileInfo, ProfileDetail, ProfileApplyResponse } from '@/types/profile'

// ========== Pipeline API ==========

/**
 * 获取 Pipeline 配置
 */
export async function getPipelineConfig(): Promise<PipelineConfig> {
  const { data } = await apiClient.get<PipelineConfig>('/config/pipeline')
  return data
}

/**
 * 更新 Pipeline 配置
 */
export async function updatePipelineConfig(
  config: Partial<PipelineConfig>
): Promise<PipelineUpdateResponse> {
  const { data } = await apiClient.put<PipelineUpdateResponse>('/config/pipeline', config)
  return data
}

// ========== Profiles API ==========

/**
 * 获取所有 Profile 列表
 */
export async function getProfiles(): Promise<ProfileInfo[]> {
  const { data } = await apiClient.get<ProfileInfo[]>('/profiles')
  return data
}

/**
 * 获取单个 Profile 详情
 */
export async function getProfile(name: string): Promise<ProfileDetail> {
  const { data } = await apiClient.get<ProfileDetail>(`/profiles/${name}`)
  return data
}

/**
 * 应用 Profile
 */
export async function applyProfile(name: string): Promise<ProfileApplyResponse> {
  const { data } = await apiClient.post<ProfileApplyResponse>(`/profiles/${name}/apply`)
  return data
}

/**
 * 创建自定义 Profile
 */
export async function createProfile(
  name: string,
  description: string,
  baseProfile: string,
  customConfig?: Partial<PipelineConfig>
): Promise<ProfileDetail> {
  const { data } = await apiClient.post<ProfileDetail>('/profiles', {
    name,
    description,
    base_profile: baseProfile,
    custom_config: customConfig
  })
  return data
}

/**
 * 删除自定义 Profile
 */
export async function deleteProfile(name: string): Promise<void> {
  await apiClient.delete(`/profiles/${name}`)
}

/**
 * 获取当前激活的 Profile
 */
export async function getActiveProfile(): Promise<ProfileDetail> {
  const { data } = await apiClient.get<ProfileDetail>('/profiles/active')
  return data
}