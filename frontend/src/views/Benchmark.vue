<script setup lang="ts">
/**
 * Benchmark Page
 * 
 * 基于 simple.html 原型设计
 * 效果对比，支持表格视图、图表视图、雷达图视图
 */
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { BarChart3, Table, Radar, Play, Download } from 'lucide-vue-next'
import { runBenchmark } from '@/api/benchmark'
import type { BenchmarkResponse, BenchmarkResult } from '@/types/benchmark'

const { t } = useI18n()

// State
const viewMode = ref<'table' | 'chart' | 'radar'>('table')
const loading = ref(false)
const error = ref<string | null>(null)

// Metrics 接口定义
interface BenchmarkMetrics {
  top1_accuracy: number
  top3_accuracy: number
  top5_accuracy: number
  ndcg: number
  latency_ms: number
}

// Convert API response to internal format
function transformResults(response: BenchmarkResponse): Array<{
  config_name: string
  is_default: boolean
  metrics: BenchmarkMetrics
}> {
  return response.results.map((result: BenchmarkResult, index: number) => {
    // Calculate metrics from search results
    const searchResults = result.results
    const scores = searchResults.map(r => r.rerank_score ?? r.score)
    
    const top1 = scores.length > 0 ? scores[0] : 0
    const top3 = scores.length >= 3 
      ? scores.slice(0, 3).reduce((sum, s) => sum + s, 0) / 3
      : top1
    const top5 = scores.length >= 5
      ? scores.slice(0, 5).reduce((sum, s) => sum + s, 0) / 5
      : top3
    
    // Calculate NDCG (simplified)
    const ndcg = scores.length > 0
      ? scores.reduce((sum, s, i) => sum + (s / Math.log2(i + 2)), 0)
      : 0

    return {
      config_name: result.config_name,
      is_default: index === 0, // First config is default
      metrics: {
        top1_accuracy: Math.min(1, top1),
        top3_accuracy: Math.min(1, top3),
        top5_accuracy: Math.min(1, top5),
        ndcg: Math.min(1, ndcg),
        latency_ms: result.latency_ms
      }
    }
  })
}

// 模拟测试结果数据
const benchmarkResults = ref<Array<{
  config_name: string
  is_default: boolean
  metrics: BenchmarkMetrics
}>>([
  {
    config_name: 'FlashRank + Hybrid',
    is_default: true,
    metrics: {
      top1_accuracy: 0.85,
      top3_accuracy: 0.92,
      top5_accuracy: 0.96,
      ndcg: 0.82,
      latency_ms: 45
    }
  },
  {
    config_name: 'Jina Reranker',
    is_default: false,
    metrics: {
      top1_accuracy: 0.88,
      top3_accuracy: 0.94,
      top5_accuracy: 0.98,
      ndcg: 0.85,
      latency_ms: 120
    }
  },
  {
    config_name: 'Vector Only',
    is_default: false,
    metrics: {
      top1_accuracy: 0.72,
      top3_accuracy: 0.85,
      top5_accuracy: 0.92,
      ndcg: 0.71,
      latency_ms: 15
    }
  }
])

// 视图选项
const viewOptions = [
  { key: 'table', label: t('benchmark.viewTable'), icon: Table },
  { key: 'chart', label: t('benchmark.viewChart'), icon: BarChart3 },
  { key: 'radar', label: t('benchmark.viewRadar'), icon: Radar }
]

// 最大值计算（用于雷达图）
const maxValues = computed(() => ({
  top1: Math.max(...benchmarkResults.value.map(r => r.metrics.top1_accuracy)) * 100,
  top3: Math.max(...benchmarkResults.value.map(r => r.metrics.top3_accuracy)) * 100,
  top5: Math.max(...benchmarkResults.value.map(r => r.metrics.top5_accuracy)) * 100,
  ndcg: Math.max(...benchmarkResults.value.map(r => r.metrics.ndcg)) * 100,
  latency: Math.max(...benchmarkResults.value.map(r => r.metrics.latency_ms))
}))

// 雷达图数据点
const radarPoints = computed(() => {
  return benchmarkResults.value.map(result => {
    const m = result.metrics
    // 归一化到0-100百分比
    const top1 = m.top1_accuracy * 100
    const top3 = m.top3_accuracy * 100
    const top5 = m.top5_accuracy * 100
    const ndcg = m.ndcg * 100
    // 延迟反转（越低越好，所以用反向值）
    const latencyScore = Math.max(0, 100 - (m.latency_ms / maxValues.value.latency) * 50)
    
    return {
      name: result.config_name,
      is_default: result.is_default,
      values: [top1, top3, top5, ndcg, latencyScore]
    }
  })
})

// 运行测试
async function handleRun() {
  loading.value = true
  error.value = null
  
  try {
    // Use default test config - call benchmark with query
    const response = await runBenchmark({
      query: 'test query',
      configs: [
        { name: 'fast', embedding_provider: 'ollama-bge' },
        { name: 'balanced', embedding_provider: 'ollama-bge', rerank_provider: 'flashrank-tiny' },
        { name: 'accurate', embedding_provider: 'ollama-bge-m3', rerank_provider: 'flashrank' }
      ]
    })
    
    // Transform API response to internal format
    benchmarkResults.value = transformResults(response)
  } catch (err) {
    console.error('Benchmark failed:', err)
    error.value = err instanceof Error ? err.message : 'Benchmark failed'
  } finally {
    loading.value = false
  }
}

// 导出报告
function handleExport() {
  const data = JSON.stringify(benchmarkResults.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'benchmark-report.json'
  a.click()
  URL.revokeObjectURL(url)
}

// 颜色列表
const colors = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#ef4444']

// 雷达图路径计算
function getRadarPath(values: number[], size: number = 150): string {
  const center = size / 2
  const radius = size / 2 - 20
  const angleStep = (2 * Math.PI) / values.length
  
  const points = values.map((v, i) => {
    const angle = i * angleStep - Math.PI / 2
    const r = (v / 100) * radius
    const x = center + r * Math.cos(angle)
    const y = center + r * Math.sin(angle)
    return `${x},${y}`
  })
  
  return `M${points.join(' L')} Z`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-start justify-between animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ t('benchmark.title') }}</h1>
        <p class="text-muted-foreground mt-1.5">{{ t('benchmark.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
          @click="handleExport"
        >
          <Download class="h-4 w-4" />
          {{ t('benchmark.export') }}
        </button>
        <button
          class="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          :disabled="loading"
          data-testid="run-benchmark"
          @click="handleRun"
        >
          <Play class="h-4 w-4" />
          {{ loading ? t('benchmark.running') : t('benchmark.run') }}
        </button>
      </div>
    </div>

    <!-- View Mode Tabs -->
    <div class="border-b">
      <div class="flex gap-4">
        <button
          v-for="option in viewOptions"
          :key="option.key"
          :class="[
            'flex items-center gap-2 px-3 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
            viewMode === option.key
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/50'
          ]"
          @click="viewMode = option.key as typeof viewMode"
        >
          <component :is="option.icon" class="h-4 w-4" />
          {{ option.label }}
        </button>
      </div>
    </div>

    <!-- Table View -->
    <template v-if="viewMode === 'table'">
      <div class="rounded-lg border overflow-hidden">
        <table class="w-full">
          <thead class="bg-muted/50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">{{ t('benchmark.configure') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">{{ t('benchmark.top1') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">{{ t('benchmark.top3') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">{{ t('benchmark.top5') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">{{ t('benchmark.ndcg') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">{{ t('benchmark.latency') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr
              v-for="result in benchmarkResults"
              :key="result.config_name"
              class="transition-colors hover:bg-muted/30"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span
                    v-if="result.is_default"
                    class="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary"
                  >
                    {{ t('common.default') }}
                  </span>
                  <span class="font-medium">{{ result.config_name }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-right">
                <span class="font-mono tabular-nums">{{ (result.metrics.top1_accuracy * 100).toFixed(0) }}%</span>
              </td>
              <td class="px-4 py-3 text-right">
                <span class="font-mono tabular-nums">{{ (result.metrics.top3_accuracy * 100).toFixed(0) }}%</span>
              </td>
              <td class="px-4 py-3 text-right">
                <span class="font-mono tabular-nums">{{ (result.metrics.top5_accuracy * 100).toFixed(0) }}%</span>
              </td>
              <td class="px-4 py-3 text-right">
                <span class="font-mono tabular-nums">{{ result.metrics.ndcg.toFixed(2) }}</span>
              </td>
              <td class="px-4 py-3 text-right">
                <span class="font-mono tabular-nums">{{ result.metrics.latency_ms }}ms</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Chart View -->
    <template v-else-if="viewMode === 'chart'">
      <div class="rounded-lg border bg-card p-6">
        <h3 class="font-semibold mb-4">{{ t('benchmark.results') }}</h3>
        <div class="space-y-4">
          <div v-for="(result, index) in benchmarkResults" :key="result.config_name">
            <div class="flex items-center justify-between mb-1">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded" :style="{ backgroundColor: colors[index % colors.length] }" />
                <span class="text-sm font-medium">{{ result.config_name }}</span>
                <span
                  v-if="result.is_default"
                  class="rounded bg-primary/10 px-1 py-0.5 text-xs font-medium text-primary"
                >
                  {{ t('common.default') }}
                </span>
              </div>
              <span class="text-sm text-muted-foreground">{{ result.metrics.latency_ms }}ms</span>
            </div>
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="w-16 text-xs text-muted-foreground">{{ t('benchmark.top1') }}</span>
                <div class="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div class="h-full rounded-full" :style="{ width: `${result.metrics.top1_accuracy * 100}%`, backgroundColor: colors[index % colors.length] }" />
                </div>
                <span class="w-10 text-xs text-right font-mono">{{ (result.metrics.top1_accuracy * 100).toFixed(0) }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="w-16 text-xs text-muted-foreground">{{ t('benchmark.top3') }}</span>
                <div class="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div class="h-full rounded-full" :style="{ width: `${result.metrics.top3_accuracy * 100}%`, backgroundColor: colors[index % colors.length] }" />
                </div>
                <span class="w-10 text-xs text-right font-mono">{{ (result.metrics.top3_accuracy * 100).toFixed(0) }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="w-16 text-xs text-muted-foreground">{{ t('benchmark.ndcg') }}</span>
                <div class="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div class="h-full rounded-full" :style="{ width: `${result.metrics.ndcg * 100}%`, backgroundColor: colors[index % colors.length] }" />
                </div>
                <span class="w-10 text-xs text-right font-mono">{{ result.metrics.ndcg.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Radar View -->
    <template v-else-if="viewMode === 'radar'">
      <div class="rounded-lg border bg-card p-6">
        <h3 class="font-semibold mb-4">{{ t('benchmark.results') }}</h3>
        <div class="flex items-start justify-center gap-8">
          <!-- Radar Chart -->
          <div class="relative" style="width: 300px; height: 300px;">
            <svg viewBox="0 0 300 300" class="w-full h-full">
              <!-- Grid circles -->
              <circle cx="150" cy="150" r="110" fill="none" stroke="currentColor" stroke-width="0.5" class="text-muted opacity-30" />
              <circle cx="150" cy="150" r="82.5" fill="none" stroke="currentColor" stroke-width="0.5" class="text-muted opacity-30" />
              <circle cx="150" cy="150" r="55" fill="none" stroke="currentColor" stroke-width="0.5" class="text-muted opacity-30" />
              <circle cx="150" cy="150" r="27.5" fill="none" stroke="currentColor" stroke-width="0.5" class="text-muted opacity-30" />
              
              <!-- Axis lines -->
              <g class="text-muted opacity-30">
                <line x1="150" y1="150" x2="150" y2="40" stroke="currentColor" stroke-width="0.5" />
                <line x1="150" y1="150" x2="254.3" y2="92.8" stroke="currentColor" stroke-width="0.5" />
                <line x1="150" y1="150" x2="254.3" y2="207.2" stroke="currentColor" stroke-width="0.5" />
                <line x1="150" y1="150" x2="45.7" y2="207.2" stroke="currentColor" stroke-width="0.5" />
                <line x1="150" y1="150" x2="45.7" y2="92.8" stroke="currentColor" stroke-width="0.5" />
              </g>
              
              <!-- Data polygons -->
              <path
                v-for="(point, index) in radarPoints"
                :key="point.name"
                :d="getRadarPath(point.values, 300)"
                :fill="`${colors[index % colors.length]}20`"
                :stroke="colors[index % colors.length]"
                stroke-width="2"
              />
            </svg>
            
            <!-- Labels -->
            <div class="absolute top-2 left-1/2 -translate-x-1/2 text-xs font-medium">Top-1</div>
            <div class="absolute top-1/4 right-2 text-xs font-medium">Top-3</div>
            <div class="absolute bottom-1/4 right-2 text-xs font-medium">Top-5</div>
            <div class="absolute bottom-1/4 left-2 text-xs font-medium">NDCG</div>
            <div class="absolute top-2 left-2 text-xs font-medium">{{ t('benchmark.latency') }}</div>
          </div>
          
          <!-- Legend -->
          <div class="space-y-2">
            <div
              v-for="(result, index) in benchmarkResults"
              :key="result.config_name"
              class="flex items-center gap-2"
            >
              <div class="h-3 w-3 rounded" :style="{ backgroundColor: colors[index % colors.length] }" />
              <span class="text-sm">{{ result.config_name }}</span>
              <span
                v-if="result.is_default"
                class="rounded bg-primary/10 px-1 py-0.5 text-xs font-medium text-primary"
              >
                {{ t('common.default') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>