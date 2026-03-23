/**
 * Profile Types
 * 
 * 根据 Docs/23-UI-Plan.md 定义
 * 用于配置预设管理
 */

import type { PipelineConfig } from './pipeline'

// ========== Profile 名称类型 ==========

export type ProfileName = 'fast' | 'balanced' | 'accurate' | string

// ========== Profile 信息 ==========

export interface ProfileInfo {
  name: string
  description: string
  icon?: string
  is_default: boolean
  use_when?: string[]
  performance?: {
    expected_latency: string
    expected_quality: string
  }
}

export interface ProfileDetail extends ProfileInfo {
  config: PipelineConfig
}

// ========== Profile 应用响应 ==========

export interface ProfileApplyResponse {
  message: string
  previous_profile: string
  current_profile: string
}

// ========== 预设 Profile 定义 ==========

export const PREDEFINED_PROFILES: Record<'fast' | 'balanced' | 'accurate', ProfileInfo> = {
  fast: {
    name: 'fast',
    description: '响应优先，适合实时场景',
    icon: 'zap',
    is_default: false,
    use_when: [
      '实时聊天响应',
      '快速代码补全',
      '低延迟要求场景'
    ],
    performance: {
      expected_latency: '< 50ms',
      expected_quality: '中等'
    }
  },
  balanced: {
    name: 'balanced',
    description: '速度与质量平衡',
    icon: 'scale',
    is_default: true,
    use_when: [
      '一般代码搜索',
      '文档检索',
      '日常开发辅助'
    ],
    performance: {
      expected_latency: '50-100ms',
      expected_quality: '良好'
    }
  },
  accurate: {
    name: 'accurate',
    description: '质量优先，适合复杂查询',
    icon: 'target',
    is_default: false,
    use_when: [
      '复杂语义查询',
      '精确代码定位',
      '深度文档分析'
    ],
    performance: {
      expected_latency: '100-200ms',
      expected_quality: '优秀'
    }
  }
}