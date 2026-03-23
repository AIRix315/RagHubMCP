<script setup lang="ts">
/**
 * Config Page
 * 
 * 基于 simple.html 原型设计
 * 管理 Embedding、Rerank、VectorDB Provider 配置
 */
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Settings, Brain, Cpu, Database, Play, Trash2, Star, AlertCircle } from 'lucide-vue-next'
import { getProviders, setDefaultProvider, deleteProvider } from '@/api/providers'
import type { ProviderStatusInfo } from '@/types/provider'

const { t } = useI18n()

// State
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref<'embedding' | 'rerank' | 'vectordb'>('embedding')
const providers = ref<{
  embedding: ProviderStatusInfo[]
  rerank: ProviderStatusInfo[]
  vectorstore: ProviderStatusInfo[]
}>({
  embedding: [],
  rerank: [],
  vectorstore: []
})

// Tab 配置
const tabs = [
  { key: 'embedding', label: t('config.tabs.embedding'), icon: Brain },
  { key: 'rerank', label: t('config.tabs.rerank'), icon: Cpu },
  { key: 'vectordb', label: t('config.tabs.vectordb'), icon: Database }
]

// 当前 Provider 列表
const currentProviders = computed(() => {
  const key = activeTab.value === 'vectordb' ? 'vectorstore' : activeTab.value
  return providers.value[key] || []
})

// 加载 Provider 列表
async function loadProviders() {
  loading.value = true
  error.value = null
  try {
    const result = await getProviders()
    providers.value = result
  } catch (e) {
    error.value = e instanceof Error ? e.message : t('errors.loadFailed')
    console.error('Failed to load providers:', e)
  } finally {
    loading.value = false
  }
}

// 设置默认 Provider
async function handleSetDefault(name: string) {
  try {
    const providerType = activeTab.value === 'vectordb' ? 'vectorstore' : activeTab.value
    await setDefaultProvider(providerType, name)
    await loadProviders()
  } catch (e) {
    console.error('Failed to set default:', e)
  }
}

// 删除 Provider
async function handleDelete(name: string) {
  if (!confirm(t('provider.deleteConfirm'))) return
  try {
    const providerType = activeTab.value === 'vectordb' ? 'vectorstore' : activeTab.value
    await deleteProvider(providerType, name)
    await loadProviders()
  } catch (e) {
    console.error('Failed to delete:', e)
  }
}

// 测试连接
async function handleTest(name: string) {
  //TODO: 实现 Provider 测试
  console.log('Testing:', name)
}

// 编辑 Provider
function handleEdit(name: string) {
  // TODO: 实现编辑弹窗
  console.log('Editing:', name)
}

// 添加 Provider
function handleAdd() {
  // TODO: 实现添加弹窗
  console.log('Adding:', activeTab.value)
}

onMounted(() => {
  loadProviders()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <h1 class="text-2xl font-bold tracking-tight">{{ t('config.title') }}</h1>
      <p class="text-muted-foreground mt-1.5">{{ t('config.subtitle') }}</p>
    </div>

    <!-- Tabs -->
    <div class="border-b">
      <div class="flex gap-4">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="[
            'flex items-center gap-2 px-3 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
            activeTab === tab.key
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/50'
          ]"
          @click="activeTab = tab.key as typeof activeTab"
        >
          <component :is="tab.icon" class="h-4 w-4" />
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-12">
      <div class="flex items-center gap-2 text-muted-foreground">
        <div class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span>{{ t('common.loading') }}</span>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
      <div class="flex items-center gap-2">
        <AlertCircle class="h-4 w-4 text-destructive" />
        <p class="text-sm text-destructive">{{ error }}</p>
      </div>
    </div>

    <!-- Provider List -->
    <template v-else>
      <!-- Add Button -->
      <div class="flex justify-between items-center">
        <h2 class="text-base font-semibold">
          {{ activeTab === 'embedding' ? t('config.embedding.title') : activeTab === 'rerank' ? t('config.rerank.title') : t('config.vectordb.title') }}
        </h2>
        <button
          class="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          @click="handleAdd"
        >
          <Plus class="h-4 w-4" />
          {{ t('common.add') }}
        </button>
      </div>

      <!-- Provider Cards -->
      <div v-if="currentProviders.length > 0" class="space-y-3">
        <div
          v-for="provider in currentProviders"
          :key="provider.name"
          :class="[
            'rounded-lg border bg-card p-4 transition-colors',
            provider.is_default ? 'border-primary/50' : ''
          ]"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-start gap-3">
              <!-- Status Dot -->
              <div class="mt-1">
                <div
                  :class="[
                    'h-2 w-2 rounded-full',
                    provider.status === 'active' ? 'bg-green-500' :
                    provider.status === 'error' ? 'bg-red-500' :
                    'bg-gray-400'
                  ]"
                />
              </div>
              <!-- Info -->
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-medium">{{ provider.name }}</span>
                  <span
                    v-if="provider.is_default"
                    class="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary"
                  >
                    {{ t('common.default') }}
                  </span>
                </div>
                <div class="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                  <span class="rounded bg-muted px-1.5 py-0.5 text-xs font-medium">{{ provider.type }}</span>
                </div>
                <div v-if="provider.error_message" class="mt-2 text-xs text-destructive">
                  {{ provider.error_message }}
                </div>
              </div>
            </div>
            <!-- Actions -->
            <div class="flex items-center gap-1">
              <button
                class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                @click="handleTest(provider.name)"
              >
                <Play class="h-3 w-3" />
                {{ t('provider.test') }}
              </button>
              <button
                class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                @click="handleEdit(provider.name)"
              >
                <Settings class="h-3 w-3" />
                {{ t('common.edit') }}
              </button>
              <button
                v-if="!provider.is_default"
                class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                @click="handleSetDefault(provider.name)"
              >
                <Star class="h-3 w-3" />
                {{ t('provider.setDefault') }}
              </button>
              <button
                v-if="!provider.is_default"
                class="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-destructive transition-colors hover:bg-destructive/10"
                @click="handleDelete(provider.name)"
              >
                <Trash2 class="h-3 w-3" />
                {{ t('common.delete') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="rounded-lg border bg-card p-12">
        <div class="flex flex-col items-center justify-center text-center">
          <component :is="activeTab === 'embedding' ? Brain : activeTab === 'rerank' ? Cpu : Database" class="h-8 w-8 text-muted-foreground mb-3" />
          <p class="text-muted-foreground">{{ t('common.noData') }}</p>
          <button
            class="mt-4 inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            @click="handleAdd"
          >
            <Plus class="h-4 w-4" />
            {{ t('common.add') }}
          </button>
        </div>
      </div>
    </template>

    <!-- Pipeline & Profiles Links -->
    <div class="grid gap-4 md:grid-cols-2 mt-8">
      <RouterLink
        to="/config/pipeline"
        class="group flex items-center gap-4 rounded-lg border bg-card p-4 transition-colors hover:border-primary/50"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
          <Settings class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
        <div>
          <div class="font-medium">{{ t('pipeline.title') }}</div>
          <div class="text-xs text-muted-foreground mt-0.5">{{ t('pipeline.description') }}</div>
        </div>
      </RouterLink>
      <RouterLink
        to="/config/profiles"
        class="group flex items-center gap-4 rounded-lg border bg-card p-4 transition-colors hover:border-primary/50"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
          <Star class="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
        <div>
          <div class="font-medium">{{ t('profile.title') }}</div>
          <div class="text-xs text-muted-foreground mt-0.5">{{ t('profile.selectProfile') }}</div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>