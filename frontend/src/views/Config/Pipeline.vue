<script setup lang="ts">
/**
 * Pipeline Config Page
 *
 * Visual configuration interface for RAG Pipeline.
 * Three stages: Retrieval → Rerank → Context Builder
 *
 * Reference: Docs/21-UI-Design-System.md Section 3.3
 */

import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  GitBranch,
  Save,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Settings,
  Search,
  Sparkles,
  FileText,
  Loader2,
  Check,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import PipelineVisualizer from '@/components/pipeline/PipelineVisualizer.vue'

const { t } = useI18n()

// ============================================================================
// Pipeline Configuration State
// ============================================================================

const loading = ref(false)
const saving = ref(false)
const savedMessage = ref<string | null>(null)

// Active stage for detailed config
const activeStage = ref<string | null>('retrieval')

// Pipeline configuration
const pipelineConfig = ref({
  retrieval: {
    top_k: 100,
    hybrid_enabled: true,
    vector_weight: 0.7,
    bm25_enabled: true,
  },
  rerank: {
    enabled: true,
    provider: 'onnx-minilm',
    top_k: 10,
    score_threshold: 0.3,
    strategy: 'standard',
    position_aware: {
      rank_1_3: [0.75, 0.25],
      rank_4_10: [0.60, 0.40],
      rank_11_plus: [0.40, 0.60],
    },
  },
  context: {
    enabled: true,
    max_tokens: 4000,
    deduplicate: true,
    deduplication_threshold: 0.9,
    merge_continuous: true,
    reordering: 'relevance',
  },
})

// Available options
const rerankProviders = ['onnx-tiny', 'onnx-minilm', 'hybrid-default']
const rankStrategies = [
  { value: 'standard', label: t('rerank.standard') },
  { value: 'position_aware', label: t('rerank.position_aware') },
  { value: 'diversity', label: t('rerank.diversity') },
]
const reorderingOptions = [
  { value: 'relevance', label: t('pipeline.reordering_relevance') },
  { value: 'chronological', label: t('pipeline.reordering_chronological') },
  { value: 'original', label: t('pipeline.reordering_original') },
]

// Expanded panels state
const expandedPanels = ref({
  retrieval: true,
  rerank: true,
  context: false,
})

// ============================================================================
// Computed
// ============================================================================

const stages = computed(() => [
  {
    id: 'retrieval',
    name: t('pipeline.retrieval_stage'),
    icon: Search,
    status: 'configured',
    config: pipelineConfig.value.retrieval,
  },
  {
    id: 'rerank',
    name: t('pipeline.rerank_stage'),
    icon: Sparkles,
    status: pipelineConfig.value.rerank.enabled ? 'configured' : 'disabled',
    config: pipelineConfig.value.rerank,
  },
  {
    id: 'context',
    name: t('pipeline.context_stage'),
    icon: FileText,
    status: pipelineConfig.value.context.enabled ? 'configured' : 'disabled',
    config: pipelineConfig.value.context,
  },
])

// ============================================================================
// Methods
// ============================================================================

function togglePanel(stageId: string) {
  expandedPanels.value[stageId as keyof typeof expandedPanels.value] =
    !expandedPanels.value[stageId as keyof typeof expandedPanels.value]
}

async function saveConfig() {
  saving.value = true
  savedMessage.value = null

  try {
    const response = await fetch('/api/config/pipeline', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pipelineConfig.value),
    })

    if (!response.ok) {
      throw new Error('Failed to save configuration')
    }

    savedMessage.value = t('pipeline.save_success')
    setTimeout(() => {
      savedMessage.value = null
    }, 3000)
  } catch (e) {
    console.error('Save failed:', e)
  } finally {
    saving.value = false
  }
}

function resetConfig() {
  // Reset to defaults
  pipelineConfig.value = {
    retrieval: {
      top_k: 100,
      hybrid_enabled: true,
      vector_weight: 0.7,
      bm25_enabled: true,
    },
    rerank: {
      enabled: true,
      provider: 'onnx-minilm',
      top_k: 10,
      score_threshold: 0.3,
      strategy: 'standard',
      position_aware: {
        rank_1_3: [0.75, 0.25],
        rank_4_10: [0.60, 0.40],
        rank_11_plus: [0.40, 0.60],
      },
    },
    context: {
      enabled: true,
      max_tokens: 4000,
      deduplicate: true,
      deduplication_threshold: 0.9,
      merge_continuous: true,
      reordering: 'relevance',
    },
  }
}

function onStageClick(stageId: string) {
  activeStage.value = stageId
  expandedPanels.value[stageId as keyof typeof expandedPanels.value] = true
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch('/api/config/pipeline')
    if (response.ok) {
      const data = await response.json()
      if (data) {
        pipelineConfig.value = { ...pipelineConfig.value, ...data }
      }
    }
  } catch (e) {
    console.error('Failed to load pipeline config:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <GitBranch class="h-8 w-8 text-primary" />
        <div>
          <h1 class="text-2xl font-bold tracking-tight">{{ t('pipeline.title') }}</h1>
          <p class="text-muted-foreground">{{ t('pipeline.description') }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="resetConfig">
          <RotateCcw class="mr-2 h-4 w-4" />
          {{ t('common.cancel') }}
        </Button>
        <Button @click="saveConfig" :disabled="saving">
          <Loader2 v-if="saving" class="mr-2 h-4 w-4 animate-spin" />
          <Save v-else class="mr-2 h-4 w-4" />
          {{ t('common.save') }}
        </Button>
      </div>
    </div>

    <!-- Success Message -->
    <div
      v-if="savedMessage"
      class="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 text-green-600 text-sm"
    >
      <Check class="h-4 w-4" />
      {{ savedMessage }}
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <Loader2 class="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
      <p class="mt-2 text-muted-foreground">{{ t('common.loading') }}</p>
    </div>

    <template v-else>
      <!-- Pipeline Visualizer -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">{{ t('pipeline.flow_visualization') }}</CardTitle>
        </CardHeader>
        <CardContent>
          <PipelineVisualizer
            :stages="stages"
            @stage-click="onStageClick"
          />
        </CardContent>
      </Card>

      <!-- Stage Configuration Panels -->
      <div class="space-y-4">
        <!-- ==================== Retrieval Config ==================== -->
        <Card>
          <button
            @click="togglePanel('retrieval')"
            class="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <Search class="h-5 w-5 text-primary" />
              <div class="text-left">
                <h3 class="font-semibold">{{ t('pipeline.retrieval_stage') }}</h3>
                <p class="text-sm text-muted-foreground">
                  Top-K: {{ pipelineConfig.retrieval.top_k }} |
                  {{ pipelineConfig.retrieval.hybrid_enabled ? 'Hybrid' : 'Vector only' }}
                </p>
              </div>
            </div>
            <ChevronDown v-if="!expandedPanels.retrieval" class="h-5 w-5" />
            <ChevronUp v-else class="h-5 w-5" />
          </button>

          <div v-if="expandedPanels.retrieval" class="border-t p-4 space-y-4">
            <div class="grid gap-4 md:grid-cols-2">
              <!-- Top-K -->
              <div class="space-y-2">
                <label class="text-sm font-medium">{{ t('pipeline.top_k') }}</label>
                <Input
                  v-model.number="pipelineConfig.retrieval.top_k"
                  type="number"
                  min="1"
                  max="500"
                />
              </div>

              <!-- Hybrid Search Toggle -->
              <div class="space-y-2">
                <label class="text-sm font-medium">{{ t('pipeline.hybrid_search') }}</label>
                <div class="flex items-center gap-2">
                  <input
                    v-model="pipelineConfig.retrieval.hybrid_enabled"
                    type="checkbox"
                    class="h-4 w-4"
                  />
                  <span class="text-sm text-muted-foreground">
                    {{ pipelineConfig.retrieval.hybrid_enabled ? t('common.enabled') : t('common.disabled') }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Vector Weight (when hybrid enabled) -->
            <div v-if="pipelineConfig.retrieval.hybrid_enabled" class="space-y-2">
              <label class="text-sm font-medium">{{ t('pipeline.vector_weight') }}</label>
              <div class="flex items-center gap-4">
                <Slider
                  v-model="[pipelineConfig.retrieval.vector_weight]"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  class="flex-1"
                />
                <span class="w-12 text-sm font-mono text-right">
                  {{ (pipelineConfig.retrieval.vector_weight * 100).toFixed(0) }}%
                </span>
              </div>
              <p class="text-xs text-muted-foreground">
                {{ t('pipeline.vector_weight_desc') }}
              </p>
            </div>

            <!-- BM25 Toggle -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('pipeline.bm25_enabled') }}</label>
              <div class="flex items-center gap-2">
                <input
                  v-model="pipelineConfig.retrieval.bm25_enabled"
                  type="checkbox"
                  class="h-4 w-4"
                />
                <span class="text-sm text-muted-foreground">
                  {{ pipelineConfig.retrieval.bm25_enabled ? t('common.enabled') : t('common.disabled') }}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <!-- ==================== Rerank Config ==================== -->
        <Card>
          <button
            @click="togglePanel('rerank')"
            class="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <Sparkles class="h-5 w-5 text-primary" />
              <div class="text-left">
                <h3 class="font-semibold">{{ t('pipeline.rerank_stage') }}</h3>
                <p class="text-sm text-muted-foreground">
                  {{ pipelineConfig.rerank.enabled ? pipelineConfig.rerank.provider : t('common.disabled') }}
                </p>
              </div>
            </div>
            <ChevronDown v-if="!expandedPanels.rerank" class="h-5 w-5" />
            <ChevronUp v-else class="h-5 w-5" />
          </button>

          <div v-if="expandedPanels.rerank" class="border-t p-4 space-y-4">
            <!-- Enable Rerank -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('pipeline.enable_rerank') }}</label>
              <div class="flex items-center gap-2">
                <input
                  v-model="pipelineConfig.rerank.enabled"
                  type="checkbox"
                  class="h-4 w-4"
                />
                <span class="text-sm text-muted-foreground">
                  {{ pipelineConfig.rerank.enabled ? t('common.enabled') : t('common.disabled') }}
                </span>
              </div>
            </div>

            <template v-if="pipelineConfig.rerank.enabled">
              <div class="grid gap-4 md:grid-cols-2">
                <!-- Provider -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('pipeline.rerank_provider') }}</label>
                  <Select v-model="pipelineConfig.rerank.provider">
                    <SelectTrigger>
                      <SelectValue :placeholder="t('pipeline.select_provider')" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="p in rerankProviders" :key="p" :value="p">
                        {{ p }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <!-- Top-K -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('pipeline.rerank_top_k') }}</label>
                  <Input
                    v-model.number="pipelineConfig.rerank.top_k"
                    type="number"
                    min="1"
                    max="100"
                  />
                </div>
              </div>

              <div class="grid gap-4 md:grid-cols-2">
                <!-- Score Threshold -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('rerank.score_threshold') }}</label>
                  <div class="flex items-center gap-4">
                    <Slider
                      v-model="[pipelineConfig.rerank.score_threshold]"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      class="flex-1"
                    />
                    <span class="w-12 text-sm font-mono text-right">
                      {{ pipelineConfig.rerank.score_threshold.toFixed(2) }}
                    </span>
                  </div>
                </div>

                <!-- Rank Strategy -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('rerank.rank_strategy') }}</label>
                  <Select v-model="pipelineConfig.rerank.strategy">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem
                        v-for="s in rankStrategies"
                        :key="s.value"
                        :value="s.value"
                      >
                        {{ s.label }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <!-- Position-Aware Config -->
              <div
                v-if="pipelineConfig.rerank.strategy === 'position_aware'"
                class="border rounded-lg p-4 bg-muted/30 space-y-3"
              >
                <h4 class="text-sm font-medium">{{ t('pipeline.position_aware_config') }}</h4>
                <div class="grid gap-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-muted-foreground">Rank 1-3:</span>
                    <span class="font-mono">
                      {{ (pipelineConfig.rerank.position_aware.rank_1_3[0] * 100).toFixed(0) }}% retrieval /
                      {{ (pipelineConfig.rerank.position_aware.rank_1_3[1] * 100).toFixed(0) }}% reranker
                    </span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-muted-foreground">Rank 4-10:</span>
                    <span class="font-mono">
                      {{ (pipelineConfig.rerank.position_aware.rank_4_10[0] * 100).toFixed(0) }}% retrieval /
                      {{ (pipelineConfig.rerank.position_aware.rank_4_10[1] * 100).toFixed(0) }}% reranker
                    </span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-muted-foreground">Rank 11+:</span>
                    <span class="font-mono">
                      {{ (pipelineConfig.rerank.position_aware.rank_11_plus[0] * 100).toFixed(0) }}% retrieval /
                      {{ (pipelineConfig.rerank.position_aware.rank_11_plus[1] * 100).toFixed(0) }}% reranker
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </Card>

        <!-- ==================== Context Builder Config ==================== -->
        <Card>
          <button
            @click="togglePanel('context')"
            class="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <FileText class="h-5 w-5 text-primary" />
              <div class="text-left">
                <h3 class="font-semibold">{{ t('pipeline.context_stage') }}</h3>
                <p class="text-sm text-muted-foreground">
                  Max Tokens: {{ pipelineConfig.context.max_tokens }} |
                  {{ pipelineConfig.context.deduplicate ? 'Dedup ON' : 'Dedup OFF' }}
                </p>
              </div>
            </div>
            <ChevronDown v-if="!expandedPanels.context" class="h-5 w-5" />
            <ChevronUp v-else class="h-5 w-5" />
          </button>

          <div v-if="expandedPanels.context" class="border-t p-4 space-y-4">
            <!-- Enable Context Builder -->
            <div class="space-y-2">
              <label class="text-sm font-medium">{{ t('pipeline.enable_context') }}</label>
              <div class="flex items-center gap-2">
                <input
                  v-model="pipelineConfig.context.enabled"
                  type="checkbox"
                  class="h-4 w-4"
                />
                <span class="text-sm text-muted-foreground">
                  {{ pipelineConfig.context.enabled ? t('common.enabled') : t('common.disabled') }}
                </span>
              </div>
            </div>

            <template v-if="pipelineConfig.context.enabled">
              <div class="grid gap-4 md:grid-cols-2">
                <!-- Max Tokens -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('pipeline.max_tokens') }}</label>
                  <Input
                    v-model.number="pipelineConfig.context.max_tokens"
                    type="number"
                    min="500"
                    max="16000"
                    step="500"
                  />
                </div>

                <!-- Reordering -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('pipeline.reordering') }}</label>
                  <Select v-model="pipelineConfig.context.reordering">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem
                        v-for="o in reorderingOptions"
                        :key="o.value"
                        :value="o.value"
                      >
                        {{ o.label }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div class="grid gap-4 md:grid-cols-2">
                <!-- Deduplicate -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('pipeline.deduplicate') }}</label>
                  <div class="flex items-center gap-2">
                    <input
                      v-model="pipelineConfig.context.deduplicate"
                      type="checkbox"
                      class="h-4 w-4"
                    />
                    <span class="text-sm text-muted-foreground">
                      {{ pipelineConfig.context.deduplicate ? t('common.enabled') : t('common.disabled') }}
                    </span>
                  </div>
                </div>

                <!-- Merge Continuous -->
                <div class="space-y-2">
                  <label class="text-sm font-medium">{{ t('pipeline.merge_continuous') }}</label>
                  <div class="flex items-center gap-2">
                    <input
                      v-model="pipelineConfig.context.merge_continuous"
                      type="checkbox"
                      class="h-4 w-4"
                    />
                    <span class="text-sm text-muted-foreground">
                      {{ pipelineConfig.context.merge_continuous ? t('common.enabled') : t('common.disabled') }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Deduplication Threshold -->
              <div v-if="pipelineConfig.context.deduplicate" class="space-y-2">
                <label class="text-sm font-medium">{{ t('pipeline.dedup_threshold') }}</label>
                <div class="flex items-center gap-4">
                  <Slider
                    v-model="[pipelineConfig.context.deduplication_threshold]"
                    :min="0.5"
                    :max="1"
                    :step="0.05"
                    class="flex-1"
                  />
                  <span class="w-12 text-sm font-mono text-right">
                    {{ pipelineConfig.context.deduplication_threshold.toFixed(2) }}
                  </span>
                </div>
              </div>
            </template>
          </div>
        </Card>
      </div>
    </template>
  </div>
</template>