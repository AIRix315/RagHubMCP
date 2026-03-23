<script setup lang="ts">
/**
 * Pipeline Visualizer Component
 *
 * Visualizes the RAG Pipeline flow with clickable stages.
 *
 * Reference: Docs/21-UI-Design-System.md Section 4.2
 */

import { ArrowRight, CheckCircle, XCircle, Loader2 } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'

interface Stage {
  id: string
  name: string
  icon: any
  status: 'configured' | 'disabled' | 'running' | 'error'
  config: Record<string, any>
}

defineProps<{
  stages: Stage[]
}>()

const emit = defineEmits<{
  (e: 'stage-click', stageId: string): void
}>()

function getStatusColor(status: string): string {
  switch (status) {
    case 'configured':
      return 'text-green-500'
    case 'disabled':
      return 'text-gray-400'
    case 'running':
      return 'text-blue-500'
    case 'error':
      return 'text-red-500'
    default:
      return 'text-gray-400'
  }
}

function getStatusBg(status: string): string {
  switch (status) {
    case 'configured':
      return 'bg-green-500/10 border-green-500/30'
    case 'disabled':
      return 'bg-gray-500/10 border-gray-500/30'
    case 'running':
      return 'bg-blue-500/10 border-blue-500/30'
    case 'error':
      return 'bg-red-500/10 border-red-500/30'
    default:
      return 'bg-muted border-muted'
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'configured':
      return CheckCircle
    case 'disabled':
      return XCircle
    case 'running':
      return Loader2
    case 'error':
      return XCircle
    default:
      return null
  }
}

function onStageClick(stage: Stage) {
  emit('stage-click', stage.id)
}
</script>

<template>
  <div class="flex items-center justify-center gap-2 py-4">
    <template v-for="(stage, index) in stages" :key="stage.id">
      <!-- Stage Card -->
      <button
        @click="onStageClick(stage)"
        :class="[
          'flex flex-col items-center p-4 rounded-lg border-2 transition-all hover:scale-105 cursor-pointer min-w-[120px]',
          getStatusBg(stage.status),
          stage.status === 'disabled' ? 'opacity-50' : '',
        ]"
      >
        <!-- Icon -->
        <div :class="['mb-2', getStatusColor(stage.status)]">
          <component
            :is="getStatusIcon(stage.status)"
            v-if="getStatusIcon(stage.status)"
            :class="['h-8 w-8', stage.status === 'running' ? 'animate-spin' : '']"
          />
          <component :is="stage.icon" v-else class="h-8 w-8" />
        </div>

        <!-- Name -->
        <span class="text-sm font-medium text-center">{{ stage.name }}</span>

        <!-- Status Badge -->
        <Badge
          :variant="stage.status === 'configured' ? 'default' : 'secondary'"
          class="mt-2 text-xs"
        >
          {{ stage.status }}
        </Badge>
      </button>

      <!-- Arrow -->
      <div
        v-if="index < stages.length - 1"
        class="flex items-center text-muted-foreground"
      >
        <ArrowRight class="h-6 w-6" />
      </div>
    </template>
  </div>

  <!-- Stage Summary -->
  <div class="mt-4 grid gap-2 text-sm text-muted-foreground">
    <div class="flex items-center justify-between p-2 rounded bg-muted/50">
      <span>Retrieval</span>
      <span class="font-mono text-foreground">
        top_k={{ stages[0]?.config?.top_k || 100 }}
        <span v-if="stages[0]?.config?.hybrid_enabled">
          | hybrid (vec={{ (stages[0]?.config?.vector_weight * 100).toFixed(0) }}%)
        </span>
      </span>
    </div>
    <div class="flex items-center justify-between p-2 rounded bg-muted/50">
      <span>Rerank</span>
      <span class="font-mono text-foreground">
        <template v-if="stages[1]?.config?.enabled">
          {{ stages[1]?.config?.provider }} | top_k={{ stages[1]?.config?.top_k }}
        </template>
        <template v-else>
          <Badge variant="secondary">disabled</Badge>
        </template>
      </span>
    </div>
    <div class="flex items-center justify-between p-2 rounded bg-muted/50">
      <span>Context</span>
      <span class="font-mono text-foreground">
        <template v-if="stages[2]?.config?.enabled">
          max_tokens={{ stages[2]?.config?.max_tokens }}
          <span v-if="stages[2]?.config?.deduplicate">| dedup</span>
        </template>
        <template v-else>
          <Badge variant="secondary">disabled</Badge>
        </template>
      </span>
    </div>
  </div>
</template>