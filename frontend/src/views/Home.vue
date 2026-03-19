<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Database, FileText, Layers, Clock, Activity, Settings } from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { useCollectionStore } from '@/stores/collection'
import { listIndexTasks } from '@/api'
import type { IndexTaskStatus } from '@/types'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import ProviderStatus from '@/components/dashboard/ProviderStatus.vue'

const configStore = useConfigStore()
const collectionStore = useCollectionStore()

const loading = ref(true)
const indexTasks = ref<IndexTaskStatus[]>([])

// Computed stats for index tasks
const activeTasks = computed(() =>
  indexTasks.value.filter(
    (t) => t.status === 'pending' || t.status === 'running'
  ).length
)

const completedTasksToday = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return indexTasks.value.filter((t) => {
    if (t.status !== 'completed' || !t.completed_at) return false
    const completedDate = new Date(t.completed_at)
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
    <div>
      <h1 class="text-3xl font-bold tracking-tight">RagHubMCP 控制台</h1>
      <p class="text-muted-foreground mt-2">通用代码 RAG 中枢 - 效果对比仪表盘</p>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="flex items-center justify-center p-8"
    >
      <span class="text-muted-foreground">加载中...</span>
    </div>

    <!-- Error State -->
    <div
      v-if="configStore.error"
      class="rounded-lg border border-destructive bg-destructive/10 p-4"
    >
      <p class="text-destructive">{{ configStore.error }}</p>
    </div>

    <!-- Main Content -->
    <template v-if="!loading">
      <!-- Collection Statistics -->
      <section>
        <h2 class="text-lg font-semibold mb-4">Collection 统计</h2>
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Collections 总数"
            :value="collectionStore.totalCollections"
            :icon="Database"
            description="已创建的向量集合数量"
          />
          <StatsCard
            title="文档总数"
            :value="collectionStore.totalDocuments.toLocaleString()"
            :icon="FileText"
            description="所有集合中的文档数"
          />
          <StatsCard
            title="平均文档数"
            :value="collectionStore.averageDocumentsPerCollection"
            :icon="Layers"
            description="每个集合的平均文档数"
          />
          <StatsCard
            title="最后更新"
            :value="formattedLastUpdated"
            :icon="Clock"
            description="数据最后刷新时间"
          />
        </div>
      </section>

      <!-- Index Task Statistics -->
      <section>
        <h2 class="text-lg font-semibold mb-4">索引任务状态</h2>
        <div class="grid gap-4 md:grid-cols-3">
          <StatsCard
            title="活跃任务"
            :value="activeTasks"
            :icon="Activity"
            :variant="activeTasks > 0 ? 'primary' : 'default'"
            :description="activeTasks > 0 ? '有任务正在处理' : '无活跃任务'"
          />
          <StatsCard
            title="今日完成"
            :value="completedTasksToday"
            :icon="FileText"
            variant="success"
            description="今日完成的索引任务"
          />
          <StatsCard
            title="总任务数"
            :value="indexTasks.length"
            :icon="Layers"
            description="历史任务总数"
          />
        </div>

        <!-- Active Tasks List -->
        <div
          v-if="activeTasks > 0"
          class="mt-4 rounded-lg border bg-card p-4"
        >
          <h3 class="font-medium mb-3">进行中的任务</h3>
          <div class="space-y-2">
            <div
              v-for="task in indexTasks.filter(t => t.status === 'pending' || t.status === 'running')"
              :key="task.task_id"
              class="flex items-center justify-between p-3 rounded-lg bg-muted/50"
            >
              <div class="flex-1 min-w-0">
                <p class="font-medium truncate">{{ task.task_id.slice(0, 8) }}...</p>
                <p class="text-sm text-muted-foreground truncate">{{ task.message }}</p>
              </div>
              <div class="flex items-center gap-4 ml-4">
                <div class="text-right">
                  <p class="text-sm font-medium">{{ Math.round(task.progress * 100) }}%</p>
                  <p class="text-xs text-muted-foreground">
                    {{ task.processed_files }}/{{ task.total_files }} 文件
                  </p>
                </div>
                <div class="w-24 h-2 bg-muted rounded-full overflow-hidden">
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

      <!-- Provider Status & System Info -->
      <div class="grid gap-6 lg:grid-cols-2">
        <!-- Provider Status -->
        <ProviderStatus
          :providers="configStore.config?.providers"
          :loading="configStore.loading"
        />

        <!-- System Configuration -->
        <div class="rounded-lg border bg-card p-6">
          <h3 class="text-lg font-semibold mb-4">系统配置</h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between p-3 rounded-lg bg-muted/50">
              <div class="flex items-center gap-3">
                <Settings class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm">Chunk Size</span>
              </div>
              <span class="font-medium">{{ configStore.config?.indexer.chunk_size || '-' }}</span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg bg-muted/50">
              <div class="flex items-center gap-3">
                <Settings class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm">Chunk Overlap</span>
              </div>
              <span class="font-medium">{{ configStore.config?.indexer.chunk_overlap || '-' }}</span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg bg-muted/50">
              <div class="flex items-center gap-3">
                <Settings class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm">Max File Size</span>
              </div>
              <span class="font-medium">
                {{ configStore.config?.indexer.max_file_size 
                  ? `${Math.round(configStore.config.indexer.max_file_size / 1024)}KB` 
                  : '-' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 rounded-lg bg-muted/50">
              <div class="flex items-center gap-3">
                <Settings class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm">支持文件类型</span>
              </div>
              <span class="font-medium text-xs">
                {{ configStore.config?.indexer.file_types?.slice(0, 4).join(', ') || '-' }}
                {{ configStore.config?.indexer.file_types && configStore.config.indexer.file_types.length > 4 
                  ? `+${configStore.config.indexer.file_types.length - 4}` 
                  : '' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <section>
        <h2 class="text-lg font-semibold mb-4">快速操作</h2>
        <div class="grid gap-4 md:grid-cols-3">
          <RouterLink
            to="/config"
            class="flex items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-muted"
          >
            <Settings class="h-5 w-5 text-muted-foreground" />
            <span class="font-medium">配置管理</span>
          </RouterLink>
          <RouterLink
            to="/collections"
            class="flex items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-muted"
          >
            <Database class="h-5 w-5 text-muted-foreground" />
            <span class="font-medium">Collection 管理</span>
          </RouterLink>
          <RouterLink
            to="/benchmark"
            class="flex items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-muted"
          >
            <Activity class="h-5 w-5 text-muted-foreground" />
            <span class="font-medium">效果对比</span>
          </RouterLink>
        </div>
      </section>
    </template>
  </div>
</template>