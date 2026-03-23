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

const { t } = useI18n()

// State
const query = ref('')
const collection = ref('default')
const topK = ref(10)
const profile = ref('balanced')
const enableRerank = ref(true)
const showAdvanced = ref(false)
const loading = ref(false)

// TODO: 实现搜索功能
function handleSearch() {
  if (!query.value.trim()) return
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1000)
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

    <!-- Results Placeholder -->
    <div class="rounded-lg border bg-card p-8">
      <div class="flex flex-col items-center justify-center text-center">
        <Search class="h-8 w-8 text-muted-foreground mb-3" />
        <p class="text-muted-foreground">{{ t('searchTest.noResults') }}</p>
      </div>
    </div>
  </div>
</template>