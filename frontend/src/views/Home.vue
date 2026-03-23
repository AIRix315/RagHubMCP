<script setup lang="ts">
/**
 * Home Page
 * 
 * 基于 simple.html 原型设计
 * 展示仪表盘统计、Provider 状态、系统配置和快速操作
 */
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Database, Activity, Settings, Zap } from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { useCollectionStore } from '@/stores/collection'
import { listIndexTasks } from '@/api'
import type { IndexTaskStatus } from '@/types'

const { t } = useI18n()
const configStore = useConfigStore()
const collectionStore = useCollectionStore()

const loading = ref(true)
const indexTasks = ref<IndexTaskStatus[]>([])

// Computed stats for index tasks
const activeTasks = computed(() =>
  indexTasks.value.filter(
    (task) => task.status === 'pending' || task.status === 'running'
  ).length
)

const completedTasksToday = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return indexTasks.value.filter((task) => {
    if (task.status !== 'completed' || !task.completed_at) return false
    const completedDate = new Date(task.completed_at)
    completedDate.setHours(0, 0, 0, 0)
    return completedDate.getTime() === today.getTime()
  }).length
})

// Format last updated time
const formattedLastUpdated = computed(() => {
  if (!collectionStore.lastUpdated) return '-'
  return collectionStore.lastUpdated.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
})

// VectorDB providers（从 config 获取）
const vectorDBDefault = computed(() => {
  // 尝试从多种可能的属性获取
  const providers = configStore.config as Record<string, unknown>
  if (!providers) return 'chroma-local'
  // 检查 providers.vectorstore 或 providers.vectordb
  const prov = providers.providers as Record<string, { default?: string }> | undefined
  if (prov?.vectorstore?.default) return prov.vectorstore.default
  if (prov?.vectordb?.default) return prov.vectordb.default
  return 'chroma-local'
})

onMounted(async () => {
  try {
    await Promise.all([
      configStore.loadConfig(),
      collectionStore.loadCollections(),
      loadIndexTasks(),
    ])
  } catch (e) {
    console.error('Failed to load dashboard data:', e)
  } finally {
    loading.value = false
  }
})

async function loadIndexTasks() {
  try {
    indexTasks.value = await listIndexTasks()
  } catch (e) {
    console.error('Failed to load index tasks:', e)
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <h1 class="text-2xl font-bold tracking-tight">{{ t('home.title') }}</h1>
      <p class="text-muted-foreground mt-1.5">{{ t('home.subtitle') }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-12">
      <div class="flex items-center gap-2 text-muted-foreground">
        <div class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span>{{ t('common.loading') }}</span>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-if="configStore.error"
      class="rounded-lg border border-destructive/50 bg-destructive/10 p-4"
    >
      <p class="text-sm text-destructive">{{ configStore.error }}</p>
    </div>

    <!-- Main Content -->
    <template v-if="!loading">
      <!-- Collection Statistics -->
      <section>
        <h2 class="text-base font-semibold mb-3">{{ t('home.stats.collections') }}</h2>
        <div class="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <div class="rounded-lg border bg-card p-4">
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.stats.collections') }}</div>
            <div class="mt-1.5 text-2xl font-bold tabular-nums">{{ collectionStore.totalCollections }}</div>
          </div>
          <div class="rounded-lg border bg-card p-4">
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.stats.documents') }}</div>
            <div class="mt-1.5 text-2xl font-bold tabular-nums">{{ collectionStore.totalDocuments.toLocaleString() }}</div>
          </div>
          <div class="rounded-lg border bg-card p-4">
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.stats.avg') }}</div>
            <div class="mt-1.5 text-2xl font-bold tabular-nums">{{ collectionStore.averageDocumentsPerCollection }}</div>
          </div>
          <div class="rounded-lg border bg-card p-4">
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.stats.updated') }}</div>
            <div class="mt-1.5 text-xl font-bold tabular-nums font-mono">{{ formattedLastUpdated }}</div>
          </div>
        </div>
      </section>

      <!-- Index Task Statistics -->
      <section>
        <h2 class="text-base font-semibold mb-3">{{ t('home.tasks.title') }}</h2>
        <div class="grid gap-3 md:grid-cols-3">
          <div 
            :class="[
              'rounded-lg border bg-card p-4',
              activeTasks > 0 ? 'border-primary/50 bg-primary/5' : ''
            ]"
          >
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.tasks.active') }}</div>
            <div :class="['mt-1.5 text-2xl font-bold tabular-nums', activeTasks > 0 ? 'text-primary' : '']">
              {{ activeTasks }}
            </div>
            <div class="text-xs text-muted-foreground mt-1">
              {{ activeTasks > 0 ? t('home.tasks.activeDesc') : t('home.tasks.totalDesc') }}
            </div>
          </div>
          <div class="rounded-lg border border-green-500/50 bg-green-500/5 p-4">
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.tasks.completed') }}</div>
            <div class="mt-1.5 text-2xl font-bold tabular-nums text-green-600">{{ completedTasksToday }}</div>
            <div class="text-xs text-muted-foreground mt-1">{{ t('home.tasks.completedDesc') }}</div>
          </div>
          <div class="rounded-lg border bg-card p-4">
            <div class="text-xs font-medium text-muted-foreground">{{ t('home.tasks.total') }}</div>
            <div class="mt-1.5 text-2xl font-bold tabular-nums">{{ indexTasks.length }}</div>
            <div class="text-xs text-muted-foreground mt-1">{{ t('home.tasks.totalDesc') }}</div>
          </div>
        </div>

        <!-- Active Tasks List -->
        <div v-if="activeTasks > 0" class="mt-4 rounded-lg border bg-card p-4">
          <h3 class="font-medium mb-3">{{ t('collections.indexing.activeTasks') }}</h3>
          <div class="space-y-2">
            <div
              v-for="task in indexTasks.filter(t => t.status === 'pending' || t.status === 'running')"
              :key="task.task_id"
              class="flex items-center justify-between gap-4 rounded-lg bg-muted/50 p-3"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <div class="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <p class="font-mono text-sm font-medium truncate">{{ task.task_id.slice(0, 8) }}</p>
                </div>
                <p class="text-xs text-muted-foreground truncate mt-0.5">{{ task.message }}</p>
              </div>
              <div class="flex items-center gap-4">
                <div class="text-right">
                  <p class="text-sm font-medium tabular-nums">{{ Math.round(task.progress * 100) }}%</p>
                  <p class="text-xs text-muted-foreground">
                    {{ task.processed_files }}/{{ task.total_files }}
                  </p>
                </div>
                <div class="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    class="h-full bg-primary transition-all duration-300"
                    :style="{ width: `${task.progress * 100}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Provider Status & System Config -->
      <div class="grid gap-4 lg:grid-cols-2">
        <!-- Provider Status -->
        <div class="rounded-lg border bg-card">
          <div class="p-4 border-b">
            <h3 class="font-semibold">{{ t('home.providers.title') }}</h3>
          </div>
          <div class="p-4 space-y-2">
            <!-- Embedding Provider -->
            <div class="flex items-center justify-between rounded-lg border border-green-500/30 bg-green-500/5 p-3">
              <div class="flex items-center gap-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-md bg-green-500/10">
                  <Zap class="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <div class="text-sm font-medium">{{ t('provider.embedding') }}</div>
                  <div class="text-xs text-muted-foreground">
                    <span class="font-mono">{{ configStore.config?.providers.embedding.default || '-' }}</span>
                  </div>
                </div>
              </div>
              <span class="rounded bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600">
                {{ t('provider.status.active') }}
              </span>
            </div>
            <!-- Rerank Provider -->
            <div class="flex items-center justify-between rounded-lg border border-blue-500/30 bg-blue-500/5 p-3">
              <div class="flex items-center gap-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-md bg-blue-500/10">
                  <Activity class="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <div class="text-sm font-medium">{{ t('provider.rerank') }}</div>
                  <div class="text-xs text-muted-foreground">
                    <span class="font-mono">{{ configStore.config?.providers.rerank.default || '-' }}</span>
                  </div>
                </div>
              </div>
              <span class="rounded bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-600">
                {{ t('provider.status.active') }}
              </span>
            </div>
            <!-- VectorDB Provider -->
            <div class="flex items-center justify-between rounded-lg border border-purple-500/30 bg-purple-500/5 p-3">
              <div class="flex items-center gap-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-md bg-purple-500/10">
                  <Database class="h-4 w-4 text-purple-600" />
                </div>
                <div>
                  <div class="text-sm font-medium">{{ t('provider.vectordb') }}</div>
                  <div class="text-xs text-muted-foreground">
                    <span class="font-mono">{{ vectorDBDefault }}</span>
                  </div>
                </div>
              </div>
              <span class="rounded bg-purple-500/10 px-2 py-0.5 text-xs font-medium text-purple-600">
                {{ t('provider.status.active') }}
              </span>
            </div>
          </div>
        </div>

        <!-- System Config -->
        <div class="rounded-lg border bg-card">
          <div class="p-4 border-b">
            <h3 class="font-semibold">{{ t('home.config.title') }}</h3>
          </div>
          <div class="p-4 space-y-2">
            <div class="flex items-center justify-between rounded-lg bg-muted/50 p-3">
              <span class="text-sm">{{ t('home.config.chunkSize') }}</span>
              <span class="font-mono text-sm font-medium bg-card px-2 py-0.5 rounded">{{ configStore.config?.indexer.chunk_size || '-' }}</span>
            </div>
            <div class="flex items-center justify-between rounded-lg bg-muted/50 p-3">
              <span class="text-sm">{{ t('home.config.overlap') }}</span>
              <span class="font-mono text-sm font-medium bg-card px-2 py-0.5 rounded">{{ configStore.config?.indexer.chunk_overlap || '-' }}</span>
            </div>
            <div class="flex items-center justify-between rounded-lg bg-muted/50 p-3">
              <span class="text-sm">{{ t('home.config.maxSize') }}</span>
              <span class="font-mono text-sm font-medium bg-card px-2 py-0.5 rounded">
                {{ configStore.config?.indexer.max_file_size 
                  ? `${Math.round(configStore.config.indexer.max_file_size / 1024)}KB` 
                  : '-' }}
              </span>
            </div>
            <div class="flex items-center justify-between rounded-lg bg-muted/50 p-3">
              <span class="text-sm">{{ t('home.config.types') }}</span>
              <span class="font-mono text-xs font-medium bg-card px-2 py-0.5 rounded">
                {{ configStore.config?.indexer.file_types?.slice(0, 3).join(', ') || '-' }}
                {{ configStore.config?.indexer.file_types && configStore.config.indexer.file_types.length > 3 
                  ? ` +${configStore.config.indexer.file_types.length - 3}` 
                  : '' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <section>
        <h2 class="text-base font-semibold mb-3">{{ t('home.actions.title') }}</h2>
        <div class="grid gap-3 md:grid-cols-3">
          <RouterLink
            to="/config"
            class="group flex items-center gap-3 rounded-lg border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
              <Settings class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <div class="font-medium">{{ t('home.actions.config') }}</div>
              <div class="text-xs text-muted-foreground mt-0.5">{{ t('home.actions.configDesc') }}</div>
            </div>
          </RouterLink>
          <RouterLink
            to="/collections"
            class="group flex items-center gap-3 rounded-lg border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
              <Database class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <div class="font-medium">{{ t('home.actions.collections') }}</div>
              <div class="text-xs text-muted-foreground mt-0.5">{{ t('home.actions.collectionsDesc') }}</div>
            </div>
          </RouterLink>
          <RouterLink
            to="/benchmark"
            class="group flex items-center gap-3 rounded-lg border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
              <Activity class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div>
              <div class="font-medium">{{ t('home.actions.benchmark') }}</div>
              <div class="text-xs text-muted-foreground mt-0.5">{{ t('home.actions.benchmarkDesc') }}</div>
            </div>
          </RouterLink>
        </div>
      </section>
    </template>
  </div>
</template>