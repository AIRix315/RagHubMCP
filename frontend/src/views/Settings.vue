<script setup lang="ts">
/**
 * Settings Page
 * 
 * 基于 simple.html 原型设计
 * 包含系统信息、MCP 配置导出、日志查看、开发工具
 */
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Server, Database, FileText, Link, Download, Copy, Check, X, Wrench } from 'lucide-vue-next'

const { t } = useI18n()

// State
const activeTab = ref<'system' | 'mcp' | 'logs' | 'devtools'>('system')
const copied = ref(false)

// 模拟系统信息
const systemInfo = ref({
  server: 'localhost:8818',
  storage: './data/chroma',
  logLevel: 'INFO',
  apiDocs: '/docs',
  version: '2.5.2',
  uptime: '3d 14h 27m'
})

// 模拟日志数据
const logs = ref<Array<{
  id: string
  time: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  module: string
  message: string
}>>([
  { id: '1', time: '10:30:15.123', level: 'INFO', module: 'rerank', message: '加载 ONNX 模型成功' },
  { id: '2', time: '10:30:14.892', level: 'INFO', module: 'api', message: '服务启动于 8818 端口' },
  { id: '3', time: '10:30:14.500', level: 'DEBUG', module: 'config', message: '加载配置文件 config.yaml' },
  { id: '4', time: '10:30:13.200', level: 'WARN', module: 'chroma', message: '持久化目录不存在，创建中...' },
  { id: '5', time: '10:30:12.100', level: 'INFO', module: 'indexer', message: '初始化索引器' },
  { id: '6', time: '10:30:11.500', level: 'ERROR', module: 'provider', message: '连接超时: retrying...' }
])

// MCP 配置
const mcpConfig = computed(() => ({
  mcpServers: {
    raghub: {
      command: 'python',
      args: ['-m', 'src.main'],
      cwd: './backend',
      env: {
        CONFIG_PATH: './backend/config.yaml'
      }
    }
  }
}))

// IDE 选项
const ideOptions = [
  { key: 'claude', label: t('settings.mcp.ides.claude') },
  { key: 'cursor', label: t('settings.mcp.ides.cursor') },
  { key: 'windsurf', label: t('settings.mcp.ides.windsurf') },
  { key: 'vscode', label: t('settings.mcp.ides.vscode') },
  { key: 'opencode', label: t('settings.mcp.ides.opencode') },
  { key: 'cherry', label: t('settings.mcp.ides.cherry') }
]
const selectedIde = ref('claude')

// 日志级别过滤
const selectedLevel = ref<string>('all')
const logLevels = [
  { key: 'all', label: t('settings.logs.levels.all') },
  { key: 'INFO', label: t('settings.logs.levels.info') },
  { key: 'WARN', label: t('settings.logs.levels.warn') },
  { key: 'ERROR', label: t('settings.logs.levels.error') },
  { key: 'DEBUG', label: t('settings.logs.levels.debug') }
]

// 过滤后的日志
const filteredLogs = computed(() => {
  if (selectedLevel.value === 'all') return logs.value
  return logs.value.filter(log => log.level === selectedLevel.value)
})

// 日志级别颜色
const levelColors: Record<string, string> = {
  INFO: 'text-blue-600 bg-blue-50',
  WARN: 'text-yellow-600 bg-yellow-50',
  ERROR: 'text-red-600 bg-red-50',
  DEBUG: 'text-gray-600 bg-gray-50'
}

// 复制配置
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(JSON.stringify(mcpConfig.value, null, 2))
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}

// 下载配置
function handleDownload() {
  const data = JSON.stringify(mcpConfig.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedIde.value}_mcp_config.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 导出日志
function handleExportLogs() {
  const data = logs.value.map(log => `[${log.time}] [${log.level}] [${log.module}] ${log.message}`).join('\n')
  const blob = new Blob([data], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'raghub_logs.txt'
  a.click()
  URL.revokeObjectURL(url)
}

// 清空日志
function handleClearLogs() {
  if (!confirm(t('settings.logs.clearConfirm'))) return
  logs.value = []
}

// ============================================================================
// DevTools Tab - Demo Data Import
// ============================================================================
const demoDataTypes = ref({
  rerankProviders: true,
  testDocuments: true,
})

const demoDataLoading = ref(false)
const demoDataLoaded = ref(false)
const demoDataMessage = ref<string | null>(null)

async function handleLoadDemoData() {
  demoDataLoading.value = true
  demoDataMessage.value = null
  
  try {
    // Dynamically import demo data
    const demoModule = await import('@/demodata/demo-rerank')
    
    // Here we would typically dispatch to stores or save to local storage
    // For now, we just show a success message
    demoDataLoaded.value = true
    demoDataMessage.value = t('settings.devtools.demoData.loadSuccess')
    
    console.log('Demo data loaded:', {
      testDocuments: demoModule.DEMO_RANK_TEST_DOCUMENTS.length,
      sampleQueries: demoModule.DEMO_RANK_SAMPLE_QUERIES.length,
      providers: demoModule.DEMO_RERANK_PROVIDERS.length,
    })
  } catch (e) {
    demoDataMessage.value = t('settings.devtools.demoData.loadError', { 
      error: e instanceof Error ? e.message : 'Unknown error' 
    })
  } finally {
    demoDataLoading.value = false
  }
}

async function handleClearDemoData() {
  if (!confirm(t('settings.devtools.clearData.confirm'))) return
  
  // Clear demo data loaded flag
  demoDataLoaded.value = false
  demoDataMessage.value = t('settings.devtools.clearData.success')
  
  // In a real implementation, this would clear data from stores/local storage
  console.log('Demo data cleared')
}

// Check if demo data is available on mount
onMounted(async () => {
  try {
    await import('@/demodata/demo-rerank')
    demoDataLoaded.value = true
  } catch {
    demoDataLoaded.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <h1 class="text-2xl font-bold tracking-tight">{{ t('settings.title') }}</h1>
      <p class="text-muted-foreground mt-1.5">{{ t('settings.subtitle') }}</p>
    </div>

    <!-- Tabs -->
    <div class="border-b">
      <div class="flex gap-4">
        <button
          v-for="tab in ['system', 'mcp', 'logs', 'devtools']"
          :key="tab"
          :class="[
            'px-3 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
            activeTab === tab
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/50'
          ]"
          @click="activeTab = tab as typeof activeTab"
        >
          <component :is="tab === 'system' ? Server : tab === 'mcp' ? Link : tab === 'logs' ? FileText : Wrench" class="h-4 w-4 inline-block mr-1.5" />
          {{ t(`settings.tabs.${tab}`) }}
        </button>
      </div>
    </div>

    <!-- System Tab -->
    <template v-if="activeTab === 'system'">
      <div class="rounded-lg border bg-card">
        <div class="p-4 border-b">
          <h3 class="font-semibold">{{ t('settings.system.title') }}</h3>
        </div>
        <div class="p-4">
          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-lg border p-4">
              <div class="flex items-center gap-3 mb-2">
                <Server class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm text-muted-foreground">{{ t('settings.system.server') }}</span>
              </div>
              <div class="font-mono font-medium">{{ systemInfo.server }}</div>
            </div>
            <div class="rounded-lg border p-4">
              <div class="flex items-center gap-3 mb-2">
                <Database class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm text-muted-foreground">{{ t('settings.system.storage') }}</span>
              </div>
              <div class="font-mono font-medium">{{ systemInfo.storage }}</div>
            </div>
            <div class="rounded-lg border p-4">
              <div class="flex items-center gap-3 mb-2">
                <FileText class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm text-muted-foreground">{{ t('settings.system.logLevel') }}</span>
              </div>
              <div class="font-medium">{{ systemInfo.logLevel }}</div>
            </div>
            <div class="rounded-lg border p-4">
              <div class="flex items-center gap-3 mb-2">
                <Link class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm text-muted-foreground">{{ t('settings.system.apiDocs') }}</span>
              </div>
              <div>
                <a href="/docs" class="font-mono font-medium text-primary hover:underline">{{ systemInfo.apiDocs }}</a>
              </div>
            </div>
            <div class="rounded-lg border p-4">
              <div class="text-sm text-muted-foreground mb-2">{{ t('settings.system.version') }}</div>
              <div class="font-mono font-medium">{{ systemInfo.version }}</div>
            </div>
            <div class="rounded-lg border p-4">
              <div class="text-sm text-muted-foreground mb-2">{{ t('settings.system.uptime') }}</div>
              <div class="font-mono font-medium">{{ systemInfo.uptime }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- MCP Tab -->
    <template v-else-if="activeTab === 'mcp'">
      <div class="rounded-lg border bg-card">
        <div class="p-4 border-b">
          <h3 class="font-semibold">{{ t('settings.mcp.title') }}</h3>
          <p class="text-sm text-muted-foreground mt-1">{{ t('settings.mcp.description') }}</p>
        </div>
        <div class="p-4">
          <!-- IDE 选择 -->
          <div class="mb-4">
            <label class="text-sm font-medium mb-2 block">{{ t('settings.mcp.chooseIDE') }}</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="ide in ideOptions"
                :key="ide.key"
                :class="[
                  'rounded px-3 py-1.5 text-sm font-medium transition-colors',
                  selectedIde === ide.key
                    ? 'bg-primary text-primary-foreground'
                    : 'border bg-background hover:bg-muted'
                ]"
                @click="selectedIde = ide.key"
              >
                {{ ide.label }}
              </button>
            </div>
          </div>

          <!-- 配置预览 -->
          <div class="rounded-lg bg-muted p-4 overflow-x-auto">
            <pre class="text-sm font-mono">{{ JSON.stringify(mcpConfig, null, 2) }}</pre>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-2 mt-4">
            <button
              class="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
              @click="handleCopy"
            >
              <component :is="copied ? Check : Copy" class="h-4 w-4" />
              {{ copied ? t('settings.mcp.copied') : t('settings.mcp.copy') }}
            </button>
            <button
              class="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
              @click="handleDownload"
            >
              <Download class="h-4 w-4" />
              {{ t('settings.mcp.download') }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Logs Tab -->
    <template v-else-if="activeTab === 'logs'">
      <div class="rounded-lg border bg-card">
        <div class="p-4 border-b flex items-center justify-between">
          <div>
            <h3 class="font-semibold">{{ t('settings.logs.title') }}</h3>
          </div>
          <div class="flex items-center gap-2">
            <select
              v-model="selectedLevel"
              class="rounded-md border bg-background px-2 py-1 text-sm outline-none focus:ring-2 focus:ring-primary"
            >
              <option v-for="level in logLevels" :key="level.key" :value="level.key">
                {{ level.label }}
              </option>
            </select>
            <button
              class="inline-flex items-center gap-1.5 rounded border bg-background px-2 py-1 text-sm transition-colors hover:bg-muted"
              @click="handleExportLogs"
            >
              <Download class="h-3 w-3" />
              {{ t('settings.logs.export') }}
            </button>
            <button
              class="inline-flex items-center gap-1.5 rounded border border-destructive/50 bg-background px-2 py-1 text-sm text-destructive transition-colors hover:bg-destructive/10"
              @click="handleClearLogs"
            >
              <X class="h-3 w-3" />
              {{ t('settings.logs.clear') }}
            </button>
          </div>
        </div>
        <div class="divide-y max-h-[400px] overflow-y-auto">
          <div
            v-for="log in filteredLogs"
            :key="log.id"
            class="flex items-start gap-3 p-3 hover:bg-muted/30"
          >
            <span class="font-mono text-xs text-muted-foreground w-24">{{ log.time }}</span>
            <span
              :class="[
                'rounded px-1.5 py-0.5 text-xs font-medium',
                levelColors[log.level]
              ]"
            >
              {{ log.level }}
            </span>
            <span class="text-xs text-muted-foreground w-20">{{ log.module }}</span>
            <span class="text-sm flex-1">{{ log.message }}</span>
          </div>
          <div v-if="filteredLogs.length === 0" class="p-8 text-center text-muted-foreground">
            {{ t('common.noData') }}
          </div>
        </div>
      </div>
    </template>

    <!-- DevTools Tab -->
    <template v-else-if="activeTab === 'devtools'">
      <div class="rounded-lg border bg-card">
        <div class="p-4 border-b">
          <h3 class="font-semibold">{{ t('settings.devtools.title') }}</h3>
          <p class="text-sm text-muted-foreground mt-1">{{ t('settings.devtools.description') }}</p>
        </div>
        <div class="p-4 space-y-4">
          <!-- Demo Data Import -->
          <div class="rounded-lg border p-4">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-medium">{{ t('settings.devtools.demoData.title') }}</h4>
                <p class="text-sm text-muted-foreground mt-1">{{ t('settings.devtools.demoData.description') }}</p>
              </div>
              <button
                :disabled="demoDataLoading"
                :class="[
                  'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  demoDataLoading || demoDataLoaded
                    ? 'bg-muted text-muted-foreground cursor-not-allowed'
                    : 'bg-primary text-primary-foreground hover:bg-primary/90'
                ]"
                @click="handleLoadDemoData"
              >
                <Download class="h-4 w-4" />
                {{ demoDataLoading ? t('common.loading') : demoDataLoaded ? t('settings.devtools.demoData.alreadyLoaded') : t('settings.devtools.demoData.load') }}
              </button>
            </div>
            
            <!-- Data types selection -->
            <div class="mt-4 space-y-2">
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="demoDataTypes.rerankProviders" :disabled="demoDataLoaded" class="rounded" />
                <span class="text-sm">{{ t('settings.devtools.demoData.rerankProviders') }}</span>
              </label>
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="demoDataTypes.testDocuments" :disabled="demoDataLoaded" class="rounded" />
                <span class="text-sm">{{ t('settings.devtools.demoData.testDocuments') }}</span>
              </label>
            </div>

            <!-- Status message -->
            <div v-if="demoDataMessage" :class="[
              'mt-3 text-sm rounded p-2',
              demoDataLoaded ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            ]">
              {{ demoDataMessage }}
            </div>
          </div>
          
          <!-- Clear Demo Data -->
          <div class="rounded-lg border border-destructive/50 p-4">
            <h4 class="font-medium text-destructive">{{ t('settings.devtools.clearData.title') }}</h4>
            <p class="text-sm text-muted-foreground mt-1">{{ t('settings.devtools.clearData.description') }}</p>
            <button
              class="mt-2 inline-flex items-center gap-1.5 rounded-md border border-destructive bg-background px-3 py-1.5 text-sm text-destructive transition-colors hover:bg-destructive/10"
              @click="handleClearDemoData"
            >
              <X class="h-4 w-4" />
              {{ t('settings.devtools.clearData.button') }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>