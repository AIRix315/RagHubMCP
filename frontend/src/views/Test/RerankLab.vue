<script setup lang="ts">
/**
 * Rerank Lab Page
 *
 * A testing and debugging interface for Rerank engines.
 * Provides three tabs:
 * 1. Engine Test - Test individual engines with custom query/documents
 * 2. Comparison - Compare multiple engines side by side
 * 3. Debug Panel - View detailed intermediate states
 *
 * Reference: Docs/21-UI-Design-System.md Section 3.2
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  FlaskConical,
  Play,
  GitCompare,
  Bug,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  ArrowUpDown,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Slider } from '@/components/ui/slider'
import { useRerankStore } from '@/stores/rerank'

const { t } = useI18n()
const rerankStore = useRerankStore()

// Demo data availability flag
const demoDataAvailable = ref(false)

// ============================================================================
// Tab Management
// ============================================================================
type TabId = 'test' | 'compare' | 'debug'
const activeTab = ref<TabId>('test')

const tabs = computed(() => [
  { id: 'test' as TabId, label: t('rerankLab.tabs.test'), icon: Play },
  { id: 'compare' as TabId, label: t('rerankLab.tabs.compare'), icon: GitCompare },
  { id: 'debug' as TabId, label: t('rerankLab.tabs.debug'), icon: Bug },
])

// ============================================================================
// Demo Data Loader
// ============================================================================
/**
 * Load demo data if available (demodata/ folder exists)
 * Demo data is not tracked in git - users can create it manually or
 * import via Settings > DevTools
 */
async function loadDemoData() {
  try {
    const demoModule = await import('@/demodata/demo-rerank')
    demoDataAvailable.value = true
    
    // Load demo data into refs
    testQuery.value = demoModule.DEMO_RANK_SAMPLE_QUERIES[0] || ''
    testDocuments.value = [...demoModule.DEMO_RANK_TEST_DOCUMENTS]
    sampleQueries.value = [...demoModule.DEMO_RANK_SAMPLE_QUERIES]
    compareDocuments.value = [...demoModule.DEMO_RANK_COMPARE_DOCUMENTS]
    debugDocuments.value = [...demoModule.DEMO_RANK_DEBUG_DOCUMENTS]
    
    console.log('Demo data loaded successfully')
  } catch {
    // Demo data not available - use empty defaults
    demoDataAvailable.value = false
    console.log('Demo data not available, using empty defaults')
  }
}

// ============================================================================
// Engine Test Tab
// ============================================================================
const testQuery = ref('')
const testDocuments = ref<string[]>([''])

// Smart defaults: sample queries for quick testing (loaded from demo data)
const sampleQueries = ref<string[]>([])

const selectedEngine = ref<string>('')
const testTopK = ref(5)
const testThreshold = ref(0.3)
const showAdvanced = ref(false)

const testLoading = ref(false)
const testResult = ref<TestResult | null>(null)
const testError = ref<string | null>(null)

// ============================================================================
// Comparison Tab
// ============================================================================
const compareQuery = ref('')
const compareDocuments = ref<string[]>([''])

interface TestResultItem {
  index: number
  text: string
  score: number
  rank: number
}

interface TestResult {
  results: TestResultItem[]
  latency_ms: number
  engine_info: {
    name: string
    type: string
    model: string
  }
}

// Auto-select first available engine
watch(
  () => rerankStore.providers,
  (providers) => {
    if (providers.length > 0 && !selectedEngine.value) {
      selectedEngine.value = providers[0].name
    }
  },
  { immediate: true }
)

async function runEngineTest() {
  if (!selectedEngine.value || !testQuery.value.trim()) return

  testLoading.value = true
  testError.value = null
  testResult.value = null

  try {
    const response = await fetch(`/api/providers/rerank/${selectedEngine.value}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: testQuery.value,
        documents: testDocuments.value.filter((d) => d.trim()),
        top_k: testTopK.value,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail?.message || 'Test failed')
    }

    testResult.value = await response.json()
  } catch (e) {
    testError.value = e instanceof Error ? e.message : t('rerankLab.test.failed')
  } finally {
    testLoading.value = false
  }
}

function addDocument() {
  testDocuments.value.push('')
}

function removeDocument(index: number) {
  if (testDocuments.value.length > 1) {
    testDocuments.value.splice(index, 1)
  }
}

function useSampleQuery(query: string) {
  testQuery.value = query
}

const selectedEngines = ref<string[]>([])
const compareLoading = ref(false)
const compareResult = ref<CompareResult | null>(null)
const compareError = ref<string | null>(null)

interface EngineComparison {
  engine: string
  metrics: {
    latency_ms: number
    top1_score: number
    avg_score: number
  }
  results: TestResultItem[]
}

interface CompareResult {
  query: string
  comparisons: EngineComparison[]
  total_latency_ms: number
}

async function runComparison() {
  if (selectedEngines.value.length < 2 || !compareQuery.value.trim()) return

  compareLoading.value = true
  compareError.value = null
  compareResult.value = null

  try {
    const response = await fetch('/api/providers/rerank/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: compareQuery.value,
        documents: compareDocuments.value.filter((d) => d.trim()),
        engines: selectedEngines.value,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail?.message || 'Comparison failed')
    }

    compareResult.value = await response.json()
  } catch (e) {
    compareError.value = e instanceof Error ? e.message : t('rerankLab.compare.failed')
  } finally {
    compareLoading.value = false
  }
}

function toggleEngine(name: string) {
  const index = selectedEngines.value.indexOf(name)
  if (index > -1) {
    selectedEngines.value.splice(index, 1)
  } else {
    selectedEngines.value.push(name)
  }
}

// ============================================================================
// Debug Tab
// ============================================================================
const debugQuery = ref('')
const debugDocuments = ref<string[]>([''])
const debugQueryId = ref('')
const debugInfo = ref<DebugInfo | null>(null)
const debugLoading = ref(false)
const debugExpanded = ref<string[]>([])
const debugWs = ref<WebSocket | null>(null)
const debugWsConnected = ref(false)
const debugStageEvents = ref<StageEvent[]>([])
const debugUseWebSocket = ref(true)

interface StageEvent {
  stage: string
  event: string
  data: Record<string, unknown>
  timestamp: string
}

interface DebugStage {
  name: string
  status: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  latency_ms: number
  metadata: Record<string, unknown>
}

interface DebugInfo {
  query_id: string
  stages: DebugStage[]
}

function toggleDebugStage(name: string) {
  const index = debugExpanded.value.indexOf(name)
  if (index > -1) {
    debugExpanded.value.splice(index, 1)
  } else {
    debugExpanded.value.push(name)
  }
}

function getStageIcon(status: string) {
  switch (status) {
    case 'completed':
      return CheckCircle
    case 'running':
      return Loader2
    case 'error':
      return XCircle
    default:
      return Clock
  }
}

function getStageIconClass(status: string) {
  switch (status) {
    case 'completed':
      return 'text-green-500'
    case 'running':
      return 'text-blue-500 animate-spin'
    case 'error':
      return 'text-red-500'
    default:
      return 'text-gray-400'
  }
}

// WebSocket connection for real-time debug
function connectDebugWebSocket() {
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/debug/ws`
  debugWs.value = new WebSocket(wsUrl)

  debugWs.value.onopen = () => {
    debugWsConnected.value = true
    console.log('Debug WebSocket connected')
  }

  debugWs.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleDebugMessage(data)
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }

  debugWs.value.onclose = () => {
    debugWsConnected.value = false
    console.log('Debug WebSocket disconnected')
  }

  debugWs.value.onerror = (error) => {
    console.error('Debug WebSocket error:', error)
    debugWsConnected.value = false
  }
}

function handleDebugMessage(data: Record<string, unknown>) {
  const event = data.event as string
  const stage = data.stage as string | undefined

  // Store events for display
  if (stage) {
    debugStageEvents.value.push({
      stage,
      event: data.event as string,
      data: (data.data || data.output || {}) as Record<string, unknown>,
      timestamp: data.timestamp as string,
    })
  }

  if (event === 'stage_completed') {
    // Update stage status in debugInfo
    if (debugInfo.value && stage) {
      const stageObj = debugInfo.value.stages.find((s) => s.name === stage)
      if (stageObj) {
        stageObj.status = 'completed'
        stageObj.output = (data.output || {}) as Record<string, unknown>
        stageObj.latency_ms = (data.latency_ms as number) || 0
      }
    }
  } else if (event === 'stage_started') {
    if (debugInfo.value && stage) {
      const stageObj = debugInfo.value.stages.find((s) => s.name === stage)
      if (stageObj) {
        stageObj.status = 'running'
      }
    }
  }
}

function disconnectDebugWebSocket() {
  if (debugWs.value) {
    debugWs.value.close()
    debugWs.value = null
  }
}

async function runDebugPipeline() {
  debugLoading.value = true
  try {
    if (debugUseWebSocket.value && debugWs.value) {
      // Use WebSocket for real-time updates
      debugWs.value.send(JSON.stringify({
        type: 'debug_pipeline',
        query: debugQuery.value,
        documents: debugDocuments.value.filter((d) => d.trim()),
      }))
    } else {
      // Fallback to REST API
      const response = await fetch('/api/debug/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: debugQuery.value,
          documents: debugDocuments.value.filter((d) => d.trim()),
        }),
      })

      if (response.ok) {
        const data = await response.json()
        debugQueryId.value = data.query_id

        // Simulate execution
        const simResponse = await fetch(`/api/debug/pipeline/${data.query_id}/simulate`, {
          method: 'POST',
        })

        if (simResponse.ok) {
          const debugData = await fetch(`/api/debug/pipeline/${data.query_id}`)
          if (debugData.ok) {
            debugInfo.value = await debugData.json()
          }
        }
      }
    }
  } catch (e) {
    console.error('Debug pipeline failed:', e)
  } finally {
    debugLoading.value = false
  }
}

// Lifecycle hooks
onMounted(async () => {
  rerankStore.loadProviders()
  await loadDemoData()
})

// Connect WebSocket when debug tab is active
watch(activeTab, (newTab) => {
  if (newTab === 'debug' && debugUseWebSocket.value) {
    connectDebugWebSocket()
  } else if (newTab !== 'debug') {
    disconnectDebugWebSocket()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  disconnectDebugWebSocket()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <FlaskConical class="h-8 w-8 text-primary" />
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ t('rerankLab.title') }}</h1>
        <p class="text-muted-foreground">{{ t('rerankLab.description') }}</p>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="border-b">
      <div class="flex gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === tab.id
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted',
          ]"
        >
          <component :is="tab.icon" class="h-4 w-4" />
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- ============================================================================ -->
    <!-- Engine Test Tab -->
    <!-- ============================================================================ -->
    <div v-if="activeTab === 'test'" class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-2">
        <!-- Input Panel -->
        <Card>
          <CardHeader>
            <CardTitle>{{ t('rerankLab.test.input') }}</CardTitle>
            <CardDescription>{{ t('rerankLab.test.inputDesc') }}</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Query Input -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('rerankLab.test.query') }}</label>
              <Textarea
                v-model="testQuery"
                :placeholder="t('rerankLab.test.queryPlaceholder')"
                :rows="2"
              />
              <!-- Sample queries -->
              <div class="flex flex-wrap gap-2 mt-2">
                <span class="text-xs text-muted-foreground">{{ t('rerankLab.test.samples') }}:</span>
                <button
                  v-for="sq in sampleQueries"
                  :key="sq"
                  @click="useSampleQuery(sq)"
                  class="text-xs px-2 py-0.5 rounded bg-muted hover:bg-muted/80 transition-colors"
                >
                  {{ sq }}
                </button>
              </div>
            </div>

            <!-- Engine Selection -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('rerankLab.test.engine') }}</label>
              <Select v-model="selectedEngine">
                <SelectTrigger>
                  <SelectValue :placeholder="t('rerankLab.test.selectEngine')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem
                    v-for="provider in rerankStore.providers"
                    :key="provider.name"
                    :value="provider.name"
                  >
                    {{ provider.name }}
                    <Badge variant="outline" class="ml-2 text-xs">{{ provider.type.toUpperCase() }}</Badge>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Documents -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium">{{ t('rerankLab.test.documents') }}</label>
                <Button variant="ghost" size="sm" @click="addDocument">
                  + {{ t('common.add') }}
                </Button>
              </div>
              <div class="space-y-2 max-h-60 overflow-y-auto">
                <div
                  v-for="(_, index) in testDocuments"
                  :key="index"
                  class="flex items-start gap-2"
                >
                  <span class="text-xs text-muted-foreground w-6 pt-2">{{ index + 1 }}.</span>
                  <Textarea
                    v-model="testDocuments[index]"
                    :placeholder="t('rerankLab.test.docPlaceholder', { n: index + 1 })"
                    :rows="2"
                    class="flex-1"
                  />
                  <Button
                    v-if="testDocuments.length > 1"
                    variant="ghost"
                    size="icon"
                    class="text-destructive mt-1"
                    @click="removeDocument(index)"
                  >
                    <XCircle class="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            <!-- Advanced Options (Progressive Disclosure) -->
            <div class="border rounded-lg">
              <button
                @click="showAdvanced = !showAdvanced"
                class="flex items-center justify-between w-full px-4 py-2 text-sm font-medium hover:bg-muted/50"
              >
                {{ t('rerankLab.test.advanced') }}
                <ChevronDown v-if="!showAdvanced" class="h-4 w-4" />
                <ChevronUp v-else class="h-4 w-4" />
              </button>
              <div v-if="showAdvanced" class="px-4 pb-4 space-y-4">
                <div class="space-y-2">
                  <label class="text-sm text-muted-foreground">{{ t('rerank.top_k') }}</label>
                  <div class="flex items-center gap-4">
                    <Slider 
                      :model-value="[testTopK]" 
                      @update:model-value="(v) => { if (v?.[0] !== undefined) testTopK = v[0] }"
                      :min="1" 
                      :max="20" 
                      :step="1" 
                      class="flex-1" 
                    />
                    <span class="w-8 text-sm font-mono">{{ testTopK }}</span>
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-sm text-muted-foreground">{{ t('rerank.score_threshold') }}</label>
                  <div class="flex items-center gap-4">
                    <Slider 
                      :model-value="[testThreshold]" 
                      @update:model-value="(v) => { if (v?.[0] !== undefined) testThreshold = v[0] }"
                      :min="0" 
                      :max="1" 
                      :step="0.1" 
                      class="flex-1" 
                    />
                    <span class="w-8 text-sm font-mono">{{ testThreshold.toFixed(1) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Run Button -->
            <Button
              class="w-full"
              :disabled="testLoading || !selectedEngine || !testQuery.trim()"
              @click="runEngineTest"
            >
              <Loader2 v-if="testLoading" class="mr-2 h-4 w-4 animate-spin" />
              <Play v-else class="mr-2 h-4 w-4" />
              {{ testLoading ? t('rerankLab.test.running') : t('rerankLab.test.run') }}
            </Button>
          </CardContent>
        </Card>

        <!-- Results Panel -->
        <Card>
          <CardHeader>
            <CardTitle>{{ t('rerankLab.test.results') }}</CardTitle>
            <CardDescription v-if="testResult">
              {{ t('rerankLab.test.latency') }}: {{ testResult.latency_ms.toFixed(2) }}ms
              <Badge variant="outline" class="ml-2">{{ testResult.engine_info.type.toUpperCase() }}</Badge>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <!-- Error State -->
            <div
              v-if="testError"
              class="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 text-destructive"
            >
              <XCircle class="h-5 w-5" />
              {{ testError }}
            </div>

            <!-- Empty State -->
            <div
              v-else-if="!testResult"
              class="text-center py-12 text-muted-foreground"
            >
              <Play class="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>{{ t('rerankLab.test.noResults') }}</p>
            </div>

            <!-- Results Table -->
            <div v-else class="space-y-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="w-16">{{ t('rerankLab.test.rank') }}</TableHead>
                    <TableHead>{{ t('rerankLab.test.text') }}</TableHead>
                    <TableHead class="w-24 text-right">{{ t('rerankLab.test.score') }}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow
                    v-for="result in testResult.results"
                    :key="result.rank"
                    :class="result.score >= testThreshold ? '' : 'opacity-50'"
                  >
                    <TableCell class="font-mono">
                      <Badge :variant="result.rank <= 3 ? 'default' : 'secondary'">
                        #{{ result.rank }}
                      </Badge>
                    </TableCell>
                    <TableCell class="truncate max-w-xs" :title="result.text">
                      {{ result.text }}
                    </TableCell>
                    <TableCell class="text-right font-mono">
                      <span :class="result.score >= testThreshold ? 'text-green-600' : 'text-muted-foreground'">
                        {{ result.score.toFixed(4) }}
                      </span>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              <!-- Engine Info -->
              <div class="text-xs text-muted-foreground border-t pt-4">
                {{ t('rerankLab.test.engineInfo') }}:
                {{ testResult.engine_info.name }} ({{ testResult.engine_info.model }})
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- ============================================================================ -->
    <!-- Comparison Tab -->
    <!-- ============================================================================ -->
    <div v-if="activeTab === 'compare'" class="space-y-6">
      <!-- Input Panel -->
      <Card>
        <CardHeader>
          <CardTitle>{{ t('rerankLab.compare.title') }}</CardTitle>
          <CardDescription>{{ t('rerankLab.compare.selectTwo') }}</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid gap-4 md:grid-cols-2">
            <!-- Query -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('rerankLab.test.query') }}</label>
              <Textarea
                v-model="compareQuery"
                :placeholder="t('rerankLab.test.queryPlaceholder')"
                :rows="2"
              />
            </div>

            <!-- Engine Selection -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('rerankLab.compare.engines') }}</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="provider in rerankStore.providers"
                  :key="provider.name"
                  @click="toggleEngine(provider.name)"
                  :class="[
                    'px-3 py-1.5 rounded-md border text-sm transition-colors',
                    selectedEngines.includes(provider.name)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background hover:bg-muted',
                  ]"
                >
                  {{ provider.name }}
                </button>
              </div>
              <p v-if="selectedEngines.length < 2" class="text-xs text-muted-foreground">
                {{ t('rerankLab.compare.selectAtLeast') }}
              </p>
            </div>
          </div>

          <!-- Documents -->
          <div class="space-y-2">
            <label class="text-sm font-medium">{{ t('rerankLab.test.documents') }}</label>
            <div class="grid gap-2 md:grid-cols-2">
              <Textarea
                v-for="(_, index) in compareDocuments"
                :key="index"
                v-model="compareDocuments[index]"
                :placeholder="`${t('rerankLab.test.docPlaceholder', { n: index + 1 })}`"
                :rows="2"
              />
            </div>
          </div>

          <!-- Run Button -->
          <Button
            :disabled="compareLoading || selectedEngines.length < 2 || !compareQuery.trim()"
            @click="runComparison"
          >
            <Loader2 v-if="compareLoading" class="mr-2 h-4 w-4 animate-spin" />
            <GitCompare v-else class="mr-2 h-4 w-4" />
            {{ compareLoading ? t('rerankLab.compare.running') : t('rerankLab.compare.run') }}
          </Button>
        </CardContent>
      </Card>

      <!-- Error State -->
      <div
        v-if="compareError"
        class="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 text-destructive"
      >
        <XCircle class="h-5 w-5" />
        {{ compareError }}
      </div>

      <!-- Comparison Results -->
      <div v-if="compareResult" class="space-y-6">
        <!-- Metrics Comparison -->
        <Card>
          <CardHeader>
            <CardTitle>{{ t('rerankLab.compare.metrics') }}</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{{ t('rerankLab.compare.engine') }}</TableHead>
                  <TableHead class="text-right">{{ t('rerankLab.compare.latency') }}</TableHead>
                  <TableHead class="text-right">{{ t('rerankLab.compare.top1') }}</TableHead>
                  <TableHead class="text-right">{{ t('rerankLab.compare.avgScore') }}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="comp in compareResult.comparisons" :key="comp.engine">
                  <TableCell class="font-medium">{{ comp.engine }}</TableCell>
                  <TableCell class="text-right font-mono">
                    {{ comp.metrics.latency_ms.toFixed(2) }}ms
                  </TableCell>
                  <TableCell class="text-right font-mono">
                    {{ comp.metrics.top1_score.toFixed(4) }}
                  </TableCell>
                  <TableCell class="text-right font-mono">
                    {{ comp.metrics.avg_score.toFixed(4) }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <!-- Side-by-Side Results -->
        <div class="grid gap-4 lg:grid-cols-2">
          <Card v-for="comp in compareResult.comparisons" :key="comp.engine">
            <CardHeader>
              <CardTitle class="text-base">{{ comp.engine }}</CardTitle>
              <CardDescription>
                {{ comp.metrics.latency_ms.toFixed(2) }}ms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div class="space-y-2">
                <div
                  v-for="result in comp.results.slice(0, 5)"
                  :key="result.rank"
                  class="flex items-center justify-between p-2 rounded bg-muted/50"
                >
                  <div class="flex items-center gap-2">
                    <Badge variant="outline">#{{ result.rank }}</Badge>
                    <span class="text-sm truncate max-w-[200px]" :title="result.text">
                      {{ result.text }}
                    </span>
                  </div>
                  <span class="font-mono text-sm">{{ result.score.toFixed(4) }}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>

<!-- ============================================================================ -->
<!-- Debug Tab -->
<!-- ============================================================================ -->
<div v-if="activeTab === 'debug'" class="space-y-6">
  <!-- WebSocket Status -->
  <Card v-if="debugUseWebSocket" class="border-l-4" :class="debugWsConnected ? 'border-l-green-500' : 'border-l-yellow-500'">
    <CardContent class="flex items-center justify-between py-3">
      <div class="flex items-center gap-2">
        <div :class="['w-2 h-2 rounded-full', debugWsConnected ? 'bg-green-500' : 'bg-yellow-500']" />
        <span class="text-sm text-muted-foreground">
          {{ debugWsConnected ? t('rerankLab.debug.connected') : t('rerankLab.debug.disconnected') }}
        </span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        @click="debugUseWebSocket = false"
        class="text-xs"
      >
        {{ t('rerankLab.debug.useRest') }}
      </Button>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle>{{ t('rerankLab.debug.title') }}</CardTitle>
      <CardDescription>{{ t('rerankLab.debug.description') }}</CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <!-- Query Input -->
      <div class="space-y-2">
        <label class="text-sm font-medium">{{ t('rerankLab.test.query') }}</label>
        <Textarea
          v-model="debugQuery"
          :placeholder="t('rerankLab.test.queryPlaceholder')"
          :rows="2"
        />
      </div>

      <!-- Documents -->
      <div class="space-y-2">
        <label class="text-sm font-medium">{{ t('rerankLab.test.documents') }}</label>
        <div class="grid gap-2 md:grid-cols-3">
          <Textarea
            v-for="(_, index) in debugDocuments"
            :key="index"
            v-model="debugDocuments[index]"
            :placeholder="`Doc ${index + 1}`"
            :rows="2"
          />
        </div>
      </div>

      <!-- Run Button -->
      <Button
        class="w-full"
        :disabled="debugLoading || !debugQuery.trim()"
        @click="runDebugPipeline"
      >
        <Loader2 v-if="debugLoading" class="mr-2 h-4 w-4 animate-spin" />
        <Bug v-else class="mr-2 h-4 w-4" />
        {{ debugLoading ? t('rerankLab.debug.running') : t('rerankLab.debug.run') }}
      </Button>

      <!-- Pipeline Visualization -->
      <div v-if="debugInfo" class="space-y-4">
        <!-- Stage Flow -->
        <div class="flex items-center justify-between border rounded-lg p-4">
          <template v-for="(stage, index) in debugInfo.stages" :key="stage.name">
            <div
              class="flex flex-col items-center cursor-pointer"
              @click="toggleDebugStage(stage.name)"
            >
              <component
                :is="getStageIcon(stage.status)"
                :class="['h-8 w-8', getStageIconClass(stage.status)]"
              />
              <span class="text-sm font-medium mt-1">{{ stage.name }}</span>
              <span v-if="stage.latency_ms > 0" class="text-xs text-muted-foreground">
                {{ stage.latency_ms.toFixed(0) }}ms
              </span>
            </div>
            <ArrowUpDown
              v-if="index < debugInfo.stages.length - 1"
              class="h-6 w-6 text-muted-foreground"
            />
          </template>
        </div>

        <!-- Real-time Events -->
        <div v-if="debugStageEvents.length > 0" class="border rounded-lg p-4">
          <h4 class="font-medium mb-3">{{ t('rerankLab.debug.events') }}</h4>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div
              v-for="(event, index) in debugStageEvents"
              :key="index"
              class="flex items-center gap-2 text-xs p-2 rounded bg-muted/50"
            >
              <Badge variant="outline" class="text-xs">{{ event.stage }}</Badge>
              <span class="text-muted-foreground">{{ event.event }}</span>
              <span class="ml-auto text-muted-foreground font-mono">{{ event.timestamp }}</span>
            </div>
          </div>
        </div>

        <!-- Stage Details -->
        <div class="space-y-2">
          <div
            v-for="stage in debugInfo.stages"
            :key="stage.name"
            v-show="debugExpanded.includes(stage.name)"
            class="border rounded-lg p-4 bg-muted/30"
          >
            <h4 class="font-medium mb-2">{{ stage.name }}</h4>
            <div class="grid gap-4 md:grid-cols-2 text-sm">
              <div>
                <span class="text-muted-foreground">{{ t('rerankLab.debug.input') }}:</span>
                <pre class="mt-1 p-2 rounded bg-muted text-xs overflow-x-auto">{{ JSON.stringify(stage.input, null, 2) }}</pre>
              </div>
              <div>
                <span class="text-muted-foreground">{{ t('rerankLab.debug.output') }}:</span>
                <pre class="mt-1 p-2 rounded bg-muted text-xs overflow-x-auto">{{ JSON.stringify(stage.output, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12 text-muted-foreground">
        <Bug class="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>{{ t('rerankLab.debug.noData') }}</p>
        <p class="text-sm mt-2">{{ t('rerankLab.debug.runHint') }}</p>
      </div>
    </CardContent>
  </Card>
</div>
  </div>
</template>