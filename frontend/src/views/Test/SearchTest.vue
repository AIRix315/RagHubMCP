<script setup lang="ts">
/**
 * Search Test Page
 * 
 * 根据 Docs/23-UI-Plan.md 设计
 * 实时检索测试与结果预览
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, ChevronDown, ChevronUp } from 'lucide-vue-next'
import { executeSearch } from '@/api/search'
import type { SearchResult, SearchResponse } from '@/types'

const { t } = useI18n()

// State
const query = ref('')
const collection = ref('default')
const topK = ref(10)
const profile = ref('balanced')
const enableRerank = ref(true)
const showAdvanced = ref(false)
const loading = ref(false)
const searchResults = ref<SearchResult[]>([])
const error = ref<string | null>(null)

// Search function with API integration
async function handleSearch() {
  if (!query.value.trim()) return
  
  loading.value = true
  error.value = null
  
  try {
    const response: SearchResponse = await executeSearch({
      query: query.value,
      collection_name: collection.value,
      top_k: topK.value,
      use_rerank: enableRerank.value,
    })
    searchResults.value = response.results
  } catch (err) {
    console.error('Search failed:', err)
    error.value = err instanceof Error ? err.message : 'Search failed'
    searchResults.value = []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <h1 class="text-2xl font-bold tracking-tight">{{ t('searchTest.title') }}</h1>
      <p class="text-muted-foreground mt-1.5">{{ t('searchTest.subtitle') }}</p>
    </div>

    <!-- Search Form -->
    <div class="rounded-lg border bg-card p-4">
      <!-- Query Input -->
      <div class="mb-4">
        <label class="text-sm font-medium mb-2 block">{{ t('searchTest.query') }}</label>
        <div class="flex gap-2">
          <textarea
            v-model="query"
            :placeholder="t('searchTest.queryPlaceholder')"
            rows="2"
            class="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          />
          <button
            :disabled="loading || !query.trim()"
            class="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            @click="handleSearch"
          >
            <Search class="h-4 w-4" />
            {{ loading ? t('common.loading') : t('searchTest.search') }}
          </button>
        </div>
      </div>

      <!-- Advanced Options Toggle -->
      <button
        class="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        @click="showAdvanced = !showAdvanced"
      >
        <component :is="showAdvanced ? ChevronUp : ChevronDown" class="h-4 w-4" />
        {{ t('searchTest.advanced') }}
      </button>

      <!-- Advanced Options -->
      <div v-if="showAdvanced" class="mt-4 space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium mb-1.5 block">{{ t('searchTest.collection') }}</label>
            <select
              v-model="collection"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              <option value="default">default</option>
              <option value="docs">docs</option>
              <option value="code">code</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium mb-1.5 block">{{ t('searchTest.topK') }}</label>
            <input
              v-model.number="topK"
              type="number"
              min="1"
              max="100"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            />
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium mb-1.5 block">{{ t('searchTest.profile') }}</label>
            <select
              v-model="profile"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              <option value="fast">{{ t('profile.fast') }}</option>
              <option value="balanced">{{ t('profile.balanced') }}</option>
              <option value="accurate">{{ t('profile.accurate') }}</option>
            </select>
          </div>
          <div class="flex items-end">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="enableRerank"
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span class="text-sm">{{ t('searchTest.enableRerank') }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <p class="text-destructive text-sm">{{ error }}</p>
    </div>

    <!-- Search Results -->
    <div v-else-if="searchResults.length > 0" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">{{ t('searchTest.results') }}</h2>
        <span class="text-sm text-muted-foreground">{{ searchResults.length }} {{ t('searchTest.resultsCount') }}</span>
      </div>
      <div class="rounded-lg border bg-card">
        <div
          v-for="(result, index) in searchResults"
          :key="result.id"
          class="border-b p-4 last:border-b-0"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 space-y-2">
              <p class="text-sm">{{ result.text }}</p>
              <div class="flex items-center gap-4 text-xs text-muted-foreground">
                <span v-if="result.metadata?.source">Source: {{ result.metadata.source }}</span>
                <span>Score: {{ (result.score * 100).toFixed(1) }}%</span>
                <span v-if="result.rerank_score">Rerank: {{ (result.rerank_score * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Placeholder -->
    <div v-else class="rounded-lg border bg-card p-8">
      <div class="flex flex-col items-center justify-center text-center">
        <Search class="h-8 w-8 text-muted-foreground mb-3" />
        <p class="text-muted-foreground">{{ t('searchTest.noResults') }}</p>
      </div>
    </div>
  </div>
</template>