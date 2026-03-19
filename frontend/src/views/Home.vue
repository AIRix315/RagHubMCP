<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import { listCollections } from '@/api'
import type { CollectionsListResponse } from '@/types'

const configStore = useConfigStore()
const collectionsCount = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    await configStore.loadConfig()
    const collections: CollectionsListResponse = await listCollections()
    collectionsCount.value = collections.total
  } catch (e) {
    console.error('Failed to load dashboard data:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">RagHubMCP 控制台</h1>
      <p class="text-muted-foreground mt-2">通用代码 RAG 中枢 - 效果对比仪表盘</p>
    </div>

    <!-- Stats Cards -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-lg border bg-card p-6">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-muted-foreground">Collections</span>
        </div>
        <div class="mt-2">
          <span class="text-2xl font-bold">{{ collectionsCount }}</span>
        </div>
      </div>

      <div class="rounded-lg border bg-card p-6">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-muted-foreground">Embedding Provider</span>
        </div>
        <div class="mt-2">
          <span class="text-lg font-semibold">{{ configStore.config?.providers.embedding.default || '-' }}</span>
        </div>
      </div>

      <div class="rounded-lg border bg-card p-6">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-muted-foreground">Rerank Provider</span>
        </div>
        <div class="mt-2">
          <span class="text-lg font-semibold">{{ configStore.config?.providers.rerank.default || '-' }}</span>
        </div>
      </div>

      <div class="rounded-lg border bg-card p-6">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-muted-foreground">Chunk Size</span>
        </div>
        <div class="mt-2">
          <span class="text-2xl font-bold">{{ configStore.config?.indexer.chunk_size || '-' }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="rounded-lg border bg-card p-6">
      <h2 class="text-lg font-semibold mb-4">快速操作</h2>
      <div class="grid gap-4 md:grid-cols-3">
        <RouterLink
          to="/config"
          class="flex items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-muted"
        >
          <span class="font-medium">配置管理</span>
        </RouterLink>
        <RouterLink
          to="/collections"
          class="flex items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-muted"
        >
          <span class="font-medium">Collection 管理</span>
        </RouterLink>
        <RouterLink
          to="/benchmark"
          class="flex items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-muted"
        >
          <span class="font-medium">效果对比</span>
        </RouterLink>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-8">
      <span class="text-muted-foreground">加载中...</span>
    </div>

    <!-- Error State -->
    <div v-if="configStore.error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <p class="text-destructive">{{ configStore.error }}</p>
    </div>
  </div>
</template>