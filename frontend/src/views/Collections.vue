<script setup lang="ts">
/**
 * Collections Page
 * 
 * 基于 simple.html 原型设计
 * 管理 Collections，支持文档浏览和索引状态查看
 */
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Database, FileText, Clock, Search, Plus, Trash2, Eye, RefreshCw } from 'lucide-vue-next'
import { useCollectionStore } from '@/stores/collection'

const { t } = useI18n()
const collectionStore = useCollectionStore()

// State
const loading = ref(true)
const searchQuery = ref('')
const activeTab = ref<'all' | 'documents' | 'indexing'>('all')

// Extended CollectionInfo with additional fields
interface CollectionInfoExtended {
  name: string
  count: number
  document_count?: number
  created_at?: string
  metadata?: Record<string, unknown>
}

// Computed
const collections = computed<CollectionInfoExtended[]>(() => collectionStore.collections || [])

const filteredCollections = computed(() => {
  if (!searchQuery.value) return collections.value
  const query = searchQuery.value.toLowerCase()
  return collections.value.filter(c => 
    c.name.toLowerCase().includes(query)
  )
})

const totalDocuments = computed(() => 
  collections.value.reduce((sum, c) => sum + (c.document_count || c.count || 0), 0)
)

const avgDocuments = computed(() => {
  if (collections.value.length === 0) return 0
  return Math.round(totalDocuments.value / collections.value.length)
})

// 加载数据
async function loadData() {
  loading.value = true
  try {
    await collectionStore.loadCollections()
  } catch (e) {
    console.error('Failed to load collections:', e)
  } finally {
    loading.value = false
  }
}

// 刷新
function handleRefresh() {
  loadData()
}

// 查看 Collection
function handleView(collection: CollectionInfoExtended) {
  // TODO: 导航到详情页
  console.log('View collection:', collection.name)
}

// 删除 Collection
async function handleDelete(collection: CollectionInfoExtended) {
  if (!confirm(t('collections.deleteConfirm'))) return
  // TODO: 实现删除
  console.log('Delete collection:', collection.name)
}

// 创建 Collection
function handleCreate() {
  // TODO: 实现创建弹窗
  console.log('Create collection')
}

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-start justify-between animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ t('collections.title') }}</h1>
        <p class="text-muted-foreground mt-1.5">{{ t('collections.subtitle') }}</p>
      </div>
      <button
        class="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        @click="handleCreate"
      >
        <Plus class="h-4 w-4" />
        {{ t('collections.create') }}
      </button>
    </div>

    <!-- Stats -->
    <div class="grid gap-3 md:grid-cols-3">
      <div class="rounded-lg border bg-card p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
            <Database class="h-4 w-4 text-muted-foreground" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">{{ t('home.stats.collections') }}</div>
            <div class="text-xl font-bold tabular-nums">{{ collectionStore.totalCollections }}</div>
          </div>
        </div>
      </div>
      <div class="rounded-lg border bg-card p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
            <FileText class="h-4 w-4 text-muted-foreground" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">{{ t('home.stats.documents') }}</div>
            <div class="text-xl font-bold tabular-nums">{{ totalDocuments.toLocaleString() }}</div>
          </div>
        </div>
      </div>
      <div class="rounded-lg border bg-card p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
            <Clock class="h-4 w-4 text-muted-foreground" />
          </div>
          <div>
            <div class="text-xs text-muted-foreground">{{ t('home.stats.avg') }}</div>
            <div class="text-xl font-bold tabular-nums">{{ avgDocuments }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs & Search -->
    <div class="flex items-center justify-between border-b pb-4">
      <div class="flex gap-1">
        <button
          v-for="tab in ['all', 'documents', 'indexing']"
          :key="tab"
          :class="[
            'rounded px-3 py-1.5 text-sm font-medium transition-colors',
            activeTab === tab
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          ]"
          @click="activeTab = tab as typeof activeTab"
        >
          {{ t(`collections.tabs.${tab}`) }}
        </button>
      </div>
      <div class="relative">
        <Search class="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('collections.searchPlaceholder')"
          class="rounded-md border bg-background pl-8 pr-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 w-64"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-12">
      <div class="flex items-center gap-2 text-muted-foreground">
        <div class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span>{{ t('common.loading') }}</span>
      </div>
    </div>

    <!-- Collections Table -->
    <template v-else>
      <div v-if="filteredCollections.length > 0" class="rounded-lg border overflow-hidden">
        <table class="w-full">
          <thead class="bg-muted/50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">{{ t('common.name') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">{{ t('collections.documentCount') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">{{ t('collections.createdAt') }}</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">{{ t('common.action') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr
              v-for="collection in filteredCollections"
              :key="collection.name"
              class="transition-colors hover:bg-muted/30"
            >
              <td class="px-4 py-3">
                <span class="font-medium font-mono">{{ collection.name }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="font-mono tabular-nums">{{ (collection.document_count || collection.count || 0).toLocaleString() }}</span>
              </td>
              <td class="px-4 py-3 text-muted-foreground text-sm">
                {{ formatDate(collection.created_at) }}
              </td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-1">
                  <button
                    class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    @click="handleView(collection)"
                  >
                    <Eye class="h-3 w-3" />
                    {{ t('common.view') }}
                  </button>
                  <button
                    class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-destructive transition-colors hover:bg-destructive/10"
                    @click="handleDelete(collection)"
                  >
                    <Trash2 class="h-3 w-3" />
                    {{ t('common.delete') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-else class="rounded-lg border bg-card p-12">
        <div class="flex flex-col items-center justify-center text-center">
          <Database class="h-8 w-8 text-muted-foreground mb-3" />
          <p class="text-muted-foreground">{{ t('common.noData') }}</p>
          <button
            class="mt-4 inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            @click="handleCreate"
          >
            <Plus class="h-4 w-4" />
            {{ t('collections.create') }}
          </button>
        </div>
      </div>
    </template>

    <!-- Refresh Button -->
    <div class="flex justify-end">
      <button
        class="inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        :disabled="loading"
        @click="handleRefresh"
      >
        <RefreshCw :class="['h-4 w-4', loading ? 'animate-spin' : '']" />
        {{ t('common.refresh') }}
      </button>
    </div>
  </div>
</template>