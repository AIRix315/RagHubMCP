<script setup lang="ts">
/**
 * DebugPanel Component
 * 
 * 根据 Docs/23-UI-Plan.md 4.4 设计
 * 用于展示 Pipeline 调试信息，查看各阶段中间状态
 */
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronDown, ChevronRight, Clock, Database, Search, FileText, AlertCircle } from 'lucide-vue-next'
import type { DebugInfo } from '@/types/debug'

interface Props {
  debugInfo?: DebugInfo | null
  loading?: boolean
}

interface Emits {
  (e: 'stage-click', stageName: string): void
}

const props = withDefaults(defineProps<Props>(), {
  debugInfo: null,
  loading: false
})

const emit = defineEmits<Emits>()

const { t } = useI18n()

// 展开状态
const expandedStages = ref<Set<string>>(new Set())

// 图标映射
const stageIcons: Record<string, typeof Search> = {
  retrieval: Search,
  rerank: Database,
  context_builder: FileText
}

// 延迟颜色映射
const getLatencyColor = (latencyMs: number): string => {
  if (latencyMs < 50) return 'text-green-500'
  if (latencyMs < 200) return 'text-yellow-500'
  return 'text-red-500'
}

// 状态颜色映射
const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-600',
  completed: 'bg-green-100 text-green-600',
  error: 'bg-red-100 text-red-600'
}

// 切换展开
const toggleStage = (stageName: string) => {
  if (expandedStages.value.has(stageName)) {
    expandedStages.value.delete(stageName)
  } else {
    expandedStages.value.add(stageName)
  }
}

// 展开/折叠全部
const expandAll = () => {
  props.debugInfo?.stages.forEach(s => expandedStages.value.add(s.name))
}

const collapseAll = () => {
  expandedStages.value.clear()
}

// 格式化元数据键
const formatMetadataKey = (key: string): string => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// 是否有数据
const hasData = computed(() => props.debugInfo && props.debugInfo.stages.length > 0)
</script>

<template>
  <div class="rounded-lg border bg-card">
    <!-- Header -->
    <div class="flex items-center justify-between border-b p-4">
      <div>
        <h3 class="font-semibold">{{ t('rerankLab.debug.title') }}</h3>
        <p class="text-sm text-muted-foreground">
          {{ t('rerankLab.debug.description') }}
        </p>
      </div>
      <div v-if="hasData" class="flex items-center gap-2">
        <button
          class="text-xs text-muted-foreground hover:text-foreground"
          @click="expandAll"
        >
          {{ t('rerankLab.debug.expandAll') }}
        </button>
        <span class="text-muted-foreground">|</span>
        <button
          class="text-xs text-muted-foreground hover:text-foreground"
          @click="collapseAll"
        >
          {{ t('rerankLab.debug.collapseAll') }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-8">
      <div class="flex items-center gap-2 text-muted-foreground">
        <div class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span>{{ t('common.loading') }}</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasData" class="flex flex-col items-center justify-center p-8 text-center">
      <AlertCircle class="h-8 w-8 text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">
        {{ t('rerankLab.debug.noData') }}
      </p>
    </div>

    <!-- Stages List -->
    <div v-else class="divide-y">
      <div
        v-for="stage in debugInfo?.stages"
        :key="stage.name"
        class="p-4"
      >
        <!-- Stage Header -->
        <button
          class="flex w-full items-center gap-3 text-left"
          @click="toggleStage(stage.name)"
        >
          <component 
            :is="stageIcons[stage.name] || Database" 
            class="h-5 w-5 text-muted-foreground" 
          />
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <span class="font-medium">
                {{ t(`rerankLab.debug.stages.${stage.name}`) }}
              </span>
              <span 
                :class="['rounded px-2 py-0.5 text-xs', statusColors[stage.status]]"
              >
                {{ stage.status }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-xs text-muted-foreground mt-1">
              <span :class="getLatencyColor(stage.latency_ms)">
                <Clock class="inline h-3 w-3 mr-1" />
                {{ stage.latency_ms }}ms
              </span>
            </div>
          </div>
          <ChevronDown 
            v-if="expandedStages.has(stage.name)" 
            class="h-4 w-4 text-muted-foreground" 
          />
          <ChevronRight 
            v-else 
            class="h-4 w-4 text-muted-foreground" 
          />
        </button>

        <!-- Stage Details (Expanded) -->
        <div v-if="expandedStages.has(stage.name)" class="mt-4 space-y-3 pl-8">
          <!-- Input -->
          <div class="rounded bg-muted/50 p-3">
            <h4 class="text-xs font-medium text-muted-foreground mb-2">
              {{ t('rerankLab.debug.input') }}
            </h4>
            <pre class="text-xs overflow-x-auto">{{ JSON.stringify(stage.input, null, 2) }}</pre>
          </div>

          <!-- Output -->
          <div class="rounded bg-muted/50 p-3">
            <h4 class="text-xs font-medium text-muted-foreground mb-2">
              {{ t('rerankLab.debug.output') }}
            </h4>
            <pre class="text-xs overflow-x-auto">{{ JSON.stringify(stage.output, null, 2) }}</pre>
          </div>

          <!-- Metadata -->
          <div v-if="stage.metadata" class="rounded bg-muted/50 p-3">
            <h4 class="text-xs font-medium text-muted-foreground mb-2">
              {{ t('rerankLab.debug.events') }}
            </h4>
            <div class="space-y-1">
              <div
                v-for="(value, key) in (stage.metadata as Record<string, Record<string, unknown>>)[stage.name]" 
                :key="key"
                class="flex items-center justify-between text-xs"
              >
                <span class="text-muted-foreground">{{ formatMetadataKey(String(key)) }}</span>
                <span class="font-mono">{{ value }}</span>
              </div>
            </div>
          </div>

          <!-- View Details Button -->
          <button
            class="text-xs text-primary hover:underline"
            @click="emit('stage-click', stage.name)"
          >
            {{ t('rerankLab.debug.viewDetails') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Total Latency -->
    <div v-if="hasData" class="border-t p-4">
      <div class="flex items-center justify-between text-sm">
        <span class="text-muted-foreground">{{ t('benchmark.latency') }}</span>
        <span class="font-mono font-medium">
          {{ debugInfo?.total_latency_ms }}ms
        </span>
      </div>
    </div>
  </div>
</template>