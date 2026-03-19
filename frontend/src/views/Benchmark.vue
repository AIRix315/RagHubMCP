<script setup lang="ts">
import { ref, computed } from 'vue'
import { runBenchmark, listCollections } from '@/api'
import type { BenchmarkRequest, BenchmarkResponse, BenchmarkConfig, CollectionInfo } from '@/types'
import BenchmarkChart from '@/components/charts/BenchmarkChart.vue'
import LatencyChart from '@/components/charts/LatencyChart.vue'

const query = ref('')
const collectionName = ref('')
const collections = ref<CollectionInfo[]>([])
const loading = ref(false)
const result = ref<BenchmarkResponse | null>(null)
const error = ref<string | null>(null)

// Tab state for results view
const activeTab = ref<'table' | 'charts'>('table')
const activeChart = ref<'overview' | 'latency'>('overview')

// Config form
const configs = ref<BenchmarkConfig[]>([
  { name: 'Config A', embedding_provider: 'ollama', rerank_provider: 'flashrank', top_k: 10 },
  { name: 'Config B', embedding_provider: 'ollama', rerank_provider: null, top_k: 10 },
])

// Available providers (would come from config in real app)
const embeddingProviders = ['ollama', 'openai']
const rerankProviders = ['flashrank', 'cohere', null]

// Load collections on mount
listCollections().then(res => {
  collections.value = res.collections
  if (res.collections.length > 0) {
    collectionName.value = res.collections[0].name
  }
})

function addConfig() {
  configs.value.push({
    name: `Config ${String.fromCharCode(65 + configs.value.length)}`,
    embedding_provider: 'ollama',
    rerank_provider: 'flashrank',
    top_k: 10,
  })
}

function removeConfig(index: number) {
  if (configs.value.length > 1) {
    configs.value.splice(index, 1)
  }
}

async function runBenchmarkTest() {
  if (!query.value.trim()) {
    error.value = '请输入查询内容'
    return
  }

  loading.value = true
  error.value = null
  result.value = null

  try {
    const request: BenchmarkRequest = {
      query: query.value,
      collection_name: collectionName.value || undefined,
      configs: configs.value,
    }
    result.value = await runBenchmark(request)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Benchmark 执行失败'
  } finally {
    loading.value = false
  }
}

// Find best config by latency
const bestConfig = computed(() => {
  if (!result.value) return null
  const sorted = [...result.value.results].sort((a, b) => a.latency_ms - b.latency_ms)
  return sorted[0]?.config_name
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">效果对比</h1>
      <p class="text-muted-foreground mt-2">测试不同配置的检索效果，找到最优方案</p>
    </div>

    <!-- Test Form -->
    <div class="rounded-lg border bg-card p-6">
      <h2 class="text-lg font-semibold mb-4">测试配置</h2>

      <div class="space-y-4">
        <!-- Query Input -->
        <div class="space-y-2">
          <label class="text-sm font-medium">查询内容</label>
          <textarea
            v-model="query"
            placeholder="输入测试查询..."
            rows="3"
            class="w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>

        <!-- Collection Select -->
        <div class="space-y-2">
          <label class="text-sm font-medium">Collection</label>
          <select
            v-model="collectionName"
            class="w-full rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option v-for="c in collections" :key="c.name" :value="c.name">
              {{ c.name }} ({{ c.count }} docs)
            </option>
          </select>
        </div>

        <!-- Configurations -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">对比配置</label>
            <button
              @click="addConfig"
              class="rounded-md border px-3 py-1 text-xs hover:bg-muted"
            >
              + 添加配置
            </button>
          </div>

          <div
            v-for="(config, index) in configs"
            :key="index"
            class="rounded-lg border p-4"
          >
            <div class="flex items-center justify-between mb-3">
              <input
                v-model="config.name"
                class="font-medium bg-transparent border-none outline-none"
              />
              <button
                v-if="configs.length > 1"
                @click="removeConfig(index)"
                class="text-xs text-muted-foreground hover:text-destructive"
              >
                移除
              </button>
            </div>

            <div class="grid gap-3 md:grid-cols-3">
              <div class="space-y-1">
                <label class="text-xs text-muted-foreground">Embedding Provider</label>
                <select
                  v-model="config.embedding_provider"
                  class="w-full rounded-md border bg-background px-2 py-1 text-sm"
                >
                  <option v-for="p in embeddingProviders" :key="p" :value="p">
                    {{ p }}
                  </option>
                </select>
              </div>

              <div class="space-y-1">
                <label class="text-xs text-muted-foreground">Rerank Provider</label>
                <select
                  v-model="config.rerank_provider"
                  class="w-full rounded-md border bg-background px-2 py-1 text-sm"
                >
                  <option value="">无</option>
                  <option v-for="p in rerankProviders.filter((x): x is string => x !== null)" :key="p" :value="p">
                    {{ p }}
                  </option>
                </select>
              </div>

              <div class="space-y-1">
                <label class="text-xs text-muted-foreground">Top K</label>
                <input
                  v-model.number="config.top_k"
                  type="number"
                  min="1"
                  max="100"
                  class="w-full rounded-md border bg-background px-2 py-1 text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Run Button -->
        <button
          @click="runBenchmarkTest"
          :disabled="loading || !query.trim()"
          class="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {{ loading ? '执行中...' : '开始对比测试' }}
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <p class="text-destructive">{{ error }}</p>
    </div>

    <!-- Results -->
    <div v-if="result" class="space-y-6">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">对比结果</h2>
        <span class="text-sm text-muted-foreground">
          总耗时: {{ result.total_latency_ms.toFixed(2) }}ms
        </span>
      </div>

      <!-- Tab Navigation -->
      <div class="flex border-b">
        <button
          @click="activeTab = 'table'"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'table'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
        >
          表格视图
        </button>
        <button
          @click="activeTab = 'charts'"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'charts'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
        >
          图表视图
        </button>
      </div>

      <!-- Table View -->
      <div v-if="activeTab === 'table'" class="space-y-6">
        <!-- Results Table -->
        <div class="rounded-lg border">
          <table class="w-full">
            <thead>
              <tr class="border-b bg-muted/50">
                <th class="px-4 py-3 text-left text-sm font-medium">配置名称</th>
                <th class="px-4 py-3 text-left text-sm font-medium">Embedding</th>
                <th class="px-4 py-3 text-left text-sm font-medium">Rerank</th>
                <th class="px-4 py-3 text-right text-sm font-medium">延迟 (ms)</th>
                <th class="px-4 py-3 text-right text-sm font-medium">结果数</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in result.results"
                :key="r.config_name"
                :class="[
                  'border-b last:border-0',
                  r.config_name === bestConfig ? 'bg-green-500/10' : 'hover:bg-muted/50'
                ]"
              >
                <td class="px-4 py-3 text-sm font-medium">
                  {{ r.config_name }}
                  <span v-if="r.config_name === bestConfig" class="ml-2 text-xs text-green-600">
                    (最快)
                  </span>
                </td>
                <td class="px-4 py-3 text-sm">{{ r.embedding_provider }}</td>
                <td class="px-4 py-3 text-sm">{{ r.rerank_provider || '-' }}</td>
                <td class="px-4 py-3 text-right text-sm">{{ r.latency_ms.toFixed(2) }}</td>
                <td class="px-4 py-3 text-right text-sm">{{ r.results.length }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Detailed Results -->
        <div v-for="r in result.results" :key="r.config_name" class="rounded-lg border">
          <div class="border-b bg-muted/50 px-4 py-2">
            <span class="font-medium">{{ r.config_name }}</span>
            <span class="ml-4 text-sm text-muted-foreground">{{ r.latency_ms.toFixed(2) }}ms</span>
          </div>
          <div class="max-h-64 overflow-auto">
            <table class="w-full">
              <thead class="sticky top-0 bg-background">
                <tr class="border-b">
                  <th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">#</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Score</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">内容</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in r.results" :key="item.id" class="border-b last:border-0">
                  <td class="px-4 py-2 text-sm text-muted-foreground">{{ idx + 1 }}</td>
                  <td class="px-4 py-2 text-sm font-mono">
                    {{ (item.rerank_score ?? item.score).toFixed(4) }}
                  </td>
                  <td class="px-4 py-2 text-sm truncate max-w-md">{{ item.text }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Charts View -->
      <div v-if="activeTab === 'charts'" class="space-y-6">
        <!-- Chart Type Tabs -->
        <div class="flex gap-2">
          <button
            @click="activeChart = 'overview'"
            :class="[
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              activeChart === 'overview'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            ]"
          >
            综合对比
          </button>
          <button
            @click="activeChart = 'latency'"
            :class="[
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              activeChart === 'latency'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            ]"
          >
            延迟分析
          </button>
        </div>

        <!-- Overview Chart -->
        <div v-if="activeChart === 'overview'" class="rounded-lg border bg-card p-4">
          <h3 class="text-sm font-semibold mb-4">配置对比总览</h3>
          <BenchmarkChart :results="result.results" title="延迟、分数与结果数量对比" />
        </div>

        <!-- Latency Chart -->
        <div v-if="activeChart === 'latency'" class="rounded-lg border bg-card p-4">
          <h3 class="text-sm font-semibold mb-4">延迟分布分析</h3>
          <LatencyChart :results="result.results" title="配置延迟对比（按延迟排序）" />
          
          <!-- Latency Stats -->
          <div class="mt-4 grid grid-cols-3 gap-4">
            <div class="rounded-lg border p-3">
              <div class="text-xs text-muted-foreground">最快配置</div>
              <div class="mt-1 font-semibold text-green-600">{{ bestConfig }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-xs text-muted-foreground">平均延迟</div>
              <div class="mt-1 font-semibold">
                {{ (result.results.reduce((sum, r) => sum + r.latency_ms, 0) / result.results.length).toFixed(2) }} ms
              </div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-xs text-muted-foreground">延迟范围</div>
              <div class="mt-1 font-semibold">
                {{ Math.min(...result.results.map(r => r.latency_ms)).toFixed(0) }} - {{ Math.max(...result.results.map(r => r.latency_ms)).toFixed(0) }} ms
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>