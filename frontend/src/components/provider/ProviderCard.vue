<script setup lang="ts">
/**
 * ProviderCard Component
 * 
 * 根据 Docs/23-UI-Plan.md 4.1 设计
 * 用于展示 Embedding/Rerank/VectorDB Provider 信息卡片
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  Settings, 
  Trash2, 
  Star, 
  Play,
  Cpu,
  Database,
  Brain
} from 'lucide-vue-next'
import type { ProviderType } from '@/types/provider'

interface Props {
  name: string
  type: ProviderType
  engine?: string
  status: 'active' | 'inactive' | 'error' | 'testing'
  config: Record<string, unknown>
  isDefault?: boolean
  errorMessage?: string
}

interface Emits {
  (e: 'edit'): void
  (e: 'test'): void
  (e: 'setDefault'): void
  (e: 'delete'): void
}

const props = withDefaults(defineProps<Props>(), {
  isDefault: false,
  errorMessage: undefined
})

const emit = defineEmits<Emits>()

const { t } = useI18n()

// 状态图标颜色映射
const statusColors = {
  active: 'text-green-500',
  inactive: 'text-gray-400',
  error: 'text-red-500',
  testing: 'text-yellow-500'
}

// 状态圆点颜色映射
const statusDotColors = {
  active: 'bg-green-500',
  inactive: 'bg-gray-400',
  error: 'bg-red-500',
  testing: 'bg-yellow-500'
}

// Provider 类型图标映射
const typeIcons = {
  embedding: Brain,
  rerank: Cpu,
  vectordb: Database
}

// 状态文本
const statusText = computed(() => {
  const texts = {
    active: t('provider.status.active'),
    inactive: t('provider.status.inactive'),
    error: t('provider.status.error'),
    testing: t('provider.status.testing')
  }
  return texts[props.status]
})

// 类型图标
const TypeIcon = computed(() => typeIcons[props.type] || Cpu)

// 配置键值对
const configItems = computed(() => {
  const items: Array<{ key: string; value: string }> = []
  
  // 根据类型显示不同的配置项
  if (props.type === 'embedding') {
    if (props.config.model) {
      items.push({ key: t('common.model'), value: String(props.config.model) })
    }
    if (props.config.dimension) {
      items.push({ key: t('config.embedding.dimension'), value: String(props.config.dimension) })
    }
  } else if (props.type === 'rerank') {
    if (props.engine) {
      items.push({ key: t('config.rerank.engine'), value: props.engine })
    }
    if (props.config.model) {
      items.push({ key: t('common.model'), value: String(props.config.model) })
    }
    if (props.config.batch_size) {
      items.push({ key: t('config.rerank.batchSize'), value: String(props.config.batch_size) })
    }
  } else if (props.type === 'vectordb') {
    if (props.config.persist_dir) {
      items.push({ key: t('config.vectordb.persistDir'), value: String(props.config.persist_dir) })
    }
    if (props.config.host) {
      items.push({ key: t('config.vectordb.host'), value: String(props.config.host) })
    }
    if (props.config.port) {
      items.push({ key: t('config.vectordb.port'), value: String(props.config.port) })
    }
  }
  
  return items.slice(0, 3) // 最多显示 3 个配置项
})

// 是否可删除（默认 Provider 不可删除）
const canDelete = computed(() => !props.isDefault)
</script>

<template>
  <div class="rounded-lg border bg-card p-4 transition-colors hover:border-primary/50">
    <!-- Header: 状态、名称、类型 -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-3">
        <!-- 类型图标 -->
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <component :is="TypeIcon" class="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ name }}</span>
            <span 
              v-if="isDefault" 
              class="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary"
            >
              {{ t('provider.isDefault') }}
            </span>
          </div>
          <div class="text-sm text-muted-foreground">
            {{ engine || type }}
          </div>
        </div>
      </div>
      <!-- 状态指示器 -->
      <div class="flex items-center gap-1.5">
        <div :class="['h-2 w-2 rounded-full', statusDotColors[status]]" />
        <span :class="['text-xs', statusColors[status]]">{{ statusText }}</span>
      </div>
    </div>

    <!-- 配置信息 -->
    <div class="space-y-1.5 mb-4">
      <div 
        v-for="(item, index) in configItems" 
        :key="index"
        class="flex items-center justify-between text-sm"
      >
        <span class="text-muted-foreground">{{ item.key }}</span>
        <span class="font-mono text-xs">{{ item.value }}</span>
      </div>
    </div>

    <!-- 错误信息 -->
    <div 
      v-if="status === 'error' && errorMessage"
      class="mb-3 rounded bg-destructive/10 px-2 py-1.5 text-xs text-destructive"
    >
      {{ errorMessage }}
    </div>

    <!-- 操作按钮 -->
    <div class="flex items-center gap-2">
      <button
        class="inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
        @click="emit('test')"
      >
        <Play class="h-3.5 w-3.5" />
        {{ t('provider.test') }}
      </button>
      <button
        class="inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
        @click="emit('edit')"
      >
        <Settings class="h-3.5 w-3.5" />
        {{ t('common.edit') }}
      </button>
      <button
        v-if="!isDefault"
        class="inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
        @click="emit('setDefault')"
      >
        <Star class="h-3.5 w-3.5" />
        {{ t('provider.setDefault') }}
      </button>
      <button
        v-if="canDelete"
        class="inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10"
        @click="emit('delete')"
      >
        <Trash2 class="h-3.5 w-3.5" />
        {{ t('common.delete') }}
      </button>
    </div>
  </div>
</template>