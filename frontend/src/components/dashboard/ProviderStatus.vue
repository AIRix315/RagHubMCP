<script setup lang="ts">
/**
 * ProviderStatus - Provider configuration status display component
 * 
 * Shows the current provider configuration including:
 * - Embedding provider details
 * - Rerank provider details
 * - LLM provider details
 */
import { computed } from 'vue'
import { Check, X, AlertCircle } from 'lucide-vue-next'
import type { ProvidersConfig, ProviderInstance } from '@/types'

interface Props {
  providers: ProvidersConfig | undefined
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

interface ProviderDisplay {
  name: string
  type: string
  model: string
  isDefault: boolean
}

function getProviderDisplay(
  category: { default: string; instances: ProviderInstance[] } | undefined,
  defaultName: string
): ProviderDisplay {
  if (!category) {
    return { name: defaultName, type: 'unknown', model: '-', isDefault: false }
  }
  
  const defaultInstance = category.instances.find(
    (inst) => inst.name === category.default
  )
  
  return {
    name: category.default || '-',
    type: defaultInstance?.type || '-',
    model: defaultInstance?.model || '-',
    isDefault: true,
  }
}

const embeddingProvider = computed(() =>
  getProviderDisplay(props.providers?.embedding, 'Embedding')
)

const rerankProvider = computed(() =>
  getProviderDisplay(props.providers?.rerank, 'Rerank')
)

const llmProvider = computed(() =>
  getProviderDisplay(props.providers?.llm, 'LLM')
)

function getStatusColor(name: string): string {
  if (!name || name === '-') return 'text-muted-foreground'
  return 'text-green-600'
}

function getStatusBg(name: string): string {
  if (!name || name === '-') return 'bg-muted'
  return 'bg-green-500/10'
}
</script>

<template>
  <div class="rounded-lg border bg-card p-6">
    <h3 class="text-lg font-semibold mb-4">Provider 状态</h3>
    
    <!-- Loading state -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-8"
    >
      <span class="text-muted-foreground">加载中...</span>
    </div>
    
    <!-- Provider list -->
    <div
      v-else
      class="space-y-4"
    >
      <!-- Embedding Provider -->
      <div
        class="flex items-center justify-between p-3 rounded-lg"
        :class="getStatusBg(embeddingProvider.name)"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-full"
            :class="embeddingProvider.name !== '-' ? 'bg-green-500/20' : 'bg-muted'"
          >
            <Check
              v-if="embeddingProvider.name !== '-'"
              class="h-4 w-4 text-green-600"
            />
            <AlertCircle
              v-else
              class="h-4 w-4 text-muted-foreground"
            />
          </div>
          <div>
            <p class="font-medium">Embedding</p>
            <p class="text-sm text-muted-foreground">
              {{ embeddingProvider.name }}
              <span
                v-if="embeddingProvider.model !== '-'"
                class="ml-1"
              >
                ({{ embeddingProvider.model }})
              </span>
            </p>
          </div>
        </div>
        <span
          class="text-sm font-medium"
          :class="getStatusColor(embeddingProvider.name)"
        >
          {{ embeddingProvider.type }}
        </span>
      </div>
      
      <!-- Rerank Provider -->
      <div
        class="flex items-center justify-between p-3 rounded-lg"
        :class="getStatusBg(rerankProvider.name)"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-full"
            :class="rerankProvider.name !== '-' ? 'bg-green-500/20' : 'bg-muted'"
          >
            <Check
              v-if="rerankProvider.name !== '-'"
              class="h-4 w-4 text-green-600"
            />
            <X
              v-else
              class="h-4 w-4 text-muted-foreground"
            />
          </div>
          <div>
            <p class="font-medium">Rerank</p>
            <p class="text-sm text-muted-foreground">
              {{ rerankProvider.name }}
              <span
                v-if="rerankProvider.model !== '-'"
                class="ml-1"
              >
                ({{ rerankProvider.model }})
              </span>
            </p>
          </div>
        </div>
        <span
          class="text-sm font-medium"
          :class="getStatusColor(rerankProvider.name)"
        >
          {{ rerankProvider.type }}
        </span>
      </div>
      
      <!-- LLM Provider -->
      <div
        class="flex items-center justify-between p-3 rounded-lg"
        :class="getStatusBg(llmProvider.name)"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-full"
            :class="llmProvider.name !== '-' ? 'bg-green-500/20' : 'bg-muted'"
          >
            <Check
              v-if="llmProvider.name !== '-'"
              class="h-4 w-4 text-green-600"
            />
            <X
              v-else
              class="h-4 w-4 text-muted-foreground"
            />
          </div>
          <div>
            <p class="font-medium">LLM</p>
            <p class="text-sm text-muted-foreground">
              {{ llmProvider.name }}
              <span
                v-if="llmProvider.model !== '-'"
                class="ml-1"
              >
                ({{ llmProvider.model }})
              </span>
            </p>
          </div>
        </div>
        <span
          class="text-sm font-medium"
          :class="getStatusColor(llmProvider.name)"
        >
          {{ llmProvider.type }}
        </span>
      </div>
    </div>
  </div>
</template>