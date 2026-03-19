<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
const saving = ref(false)
const saveMessage = ref<{ type: 'success' | 'error'; text: string } | null>(null)

// Embedding providers list
const embeddingProviders = computed(() => {
  return configStore.config?.providers.embedding.instances || []
})

// Rerank providers list
const rerankProviders = computed(() => {
  return configStore.config?.providers.rerank.instances || []
})

// Indexer settings
const chunkSize = ref(500)
const chunkOverlap = ref(50)
const maxFileSize = ref(1048576)

onMounted(async () => {
  await configStore.loadConfig()
  if (configStore.config) {
    chunkSize.value = configStore.config.indexer.chunk_size
    chunkOverlap.value = configStore.config.indexer.chunk_overlap
    maxFileSize.value = configStore.config.indexer.max_file_size
  }
})

async function handleSave() {
  saving.value = true
  saveMessage.value = null

  try {
    await configStore.saveConfigData({
      indexer: {
        chunk_size: chunkSize.value,
        chunk_overlap: chunkOverlap.value,
        max_file_size: maxFileSize.value,
        file_types: configStore.config?.indexer.file_types || [],
        exclude_dirs: configStore.config?.indexer.exclude_dirs || [],
      },
    })
    saveMessage.value = { type: 'success', text: '配置保存成功' }
  } catch (e) {
    saveMessage.value = { type: 'error', text: '配置保存失败' }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">配置管理</h1>
      <p class="text-muted-foreground mt-2">管理系统配置和 Provider 设置</p>
    </div>

    <!-- Loading State -->
    <div v-if="configStore.loading" class="flex items-center justify-center p-8">
      <span class="text-muted-foreground">加载中...</span>
    </div>

    <!-- Error State -->
    <div v-if="configStore.error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <p class="text-destructive">{{ configStore.error }}</p>
    </div>

    <!-- Config Form -->
    <div v-if="configStore.config" class="space-y-6">
      <!-- Embedding Provider -->
      <div class="rounded-lg border bg-card p-6">
        <h2 class="text-lg font-semibold mb-4">Embedding Provider</h2>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium">当前默认: {{ configStore.config.providers.embedding.default }}</label>
          </div>
          <div class="rounded-lg border">
            <table class="w-full">
              <thead>
                <tr class="border-b bg-muted/50">
                  <th class="px-4 py-2 text-left text-sm font-medium">名称</th>
                  <th class="px-4 py-2 text-left text-sm font-medium">类型</th>
                  <th class="px-4 py-2 text-left text-sm font-medium">模型</th>
                  <th class="px-4 py-2 text-left text-sm font-medium">维度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="provider in embeddingProviders" :key="provider.name" class="border-b last:border-0">
                  <td class="px-4 py-2 text-sm">{{ provider.name }}</td>
                  <td class="px-4 py-2 text-sm">{{ provider.type }}</td>
                  <td class="px-4 py-2 text-sm">{{ provider.model }}</td>
                  <td class="px-4 py-2 text-sm">{{ provider.dimension || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Rerank Provider -->
      <div class="rounded-lg border bg-card p-6">
        <h2 class="text-lg font-semibold mb-4">Rerank Provider</h2>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium">当前默认: {{ configStore.config.providers.rerank.default }}</label>
          </div>
          <div class="rounded-lg border">
            <table class="w-full">
              <thead>
                <tr class="border-b bg-muted/50">
                  <th class="px-4 py-2 text-left text-sm font-medium">名称</th>
                  <th class="px-4 py-2 text-left text-sm font-medium">类型</th>
                  <th class="px-4 py-2 text-left text-sm font-medium">模型</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="provider in rerankProviders" :key="provider.name" class="border-b last:border-0">
                  <td class="px-4 py-2 text-sm">{{ provider.name }}</td>
                  <td class="px-4 py-2 text-sm">{{ provider.type }}</td>
                  <td class="px-4 py-2 text-sm">{{ provider.model }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Indexer Settings -->
      <div class="rounded-lg border bg-card p-6">
        <h2 class="text-lg font-semibold mb-4">索引设置</h2>
        <div class="grid gap-4 md:grid-cols-3">
          <div class="space-y-2">
            <label class="text-sm font-medium">Chunk Size</label>
            <input
              v-model.number="chunkSize"
              type="number"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Chunk Overlap</label>
            <input
              v-model.number="chunkOverlap"
              type="number"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Max File Size (bytes)</label>
            <input
              v-model.number="maxFileSize"
              type="number"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>
        </div>

        <!-- File Types -->
        <div class="mt-4">
          <label class="text-sm font-medium">支持的文件类型</label>
          <div class="mt-2 flex flex-wrap gap-2">
            <span
              v-for="ft in configStore.config.indexer.file_types"
              :key="ft"
              class="rounded-full bg-muted px-3 py-1 text-xs"
            >
              {{ ft }}
            </span>
          </div>
        </div>

        <!-- Exclude Dirs -->
        <div class="mt-4">
          <label class="text-sm font-medium">排除目录</label>
          <div class="mt-2 flex flex-wrap gap-2">
            <span
              v-for="dir in configStore.config.indexer.exclude_dirs"
              :key="dir"
              class="rounded-full bg-muted px-3 py-1 text-xs"
            >
              {{ dir }}
            </span>
          </div>
        </div>
      </div>

      <!-- Save Button -->
      <div class="flex items-center gap-4">
        <button
          @click="handleSave"
          :disabled="saving"
          class="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存配置' }}
        </button>

        <span v-if="saveMessage" :class="saveMessage.type === 'success' ? 'text-green-600' : 'text-destructive'">
          {{ saveMessage.text }}
        </span>
      </div>
    </div>
  </div>
</template>