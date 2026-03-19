<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useConfigStore } from '@/stores/config'
import { Info, Download, RefreshCw } from 'lucide-vue-next'

const configStore = useConfigStore()

// System info
const systemInfo = ref<{
  serverHost: string
  serverPort: number
  chromaPersistDir: string
  logLevel: string
} | null>(null)

// MCP config export
const mcpConfig = computed(() => {
  if (!configStore.config) return null
  
  // Generate MCP server config for Claude Desktop
  return {
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
  }
})

const copying = ref(false)
const copyMessage = ref<string | null>(null)

onMounted(async () => {
  await configStore.loadConfig()
  if (configStore.config) {
    systemInfo.value = {
      serverHost: configStore.config.server.host,
      serverPort: configStore.config.server.port,
      chromaPersistDir: configStore.config.chroma.persist_dir,
      logLevel: configStore.config.logging.level,
    }
  }
})

async function copyMcpConfig() {
  if (!mcpConfig.value) return
  
  copying.value = true
  try {
    await navigator.clipboard.writeText(JSON.stringify(mcpConfig.value, null, 2))
    copyMessage.value = '已复制到剪贴板'
    setTimeout(() => {
      copyMessage.value = null
    }, 2000)
  } catch (e) {
    copyMessage.value = '复制失败'
  } finally {
    copying.value = false
  }
}

function downloadMcpConfig() {
  if (!mcpConfig.value) return
  
  const blob = new Blob([JSON.stringify(mcpConfig.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'claude_desktop_config.json'
  a.click()
  URL.revokeObjectURL(url)
}

async function refreshConfig() {
  await configStore.loadConfig()
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">系统设置</h1>
      <p class="text-muted-foreground mt-2">查看系统信息和导出 MCP 配置</p>
    </div>

    <!-- Loading State -->
    <div v-if="configStore.loading" class="flex items-center justify-center p-8">
      <span class="text-muted-foreground">加载中...</span>
    </div>

    <!-- Error State -->
    <div v-if="configStore.error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <p class="text-destructive">{{ configStore.error }}</p>
    </div>

    <div v-if="configStore.config" class="space-y-6">
      <!-- System Info -->
      <div class="rounded-lg border bg-card p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <Info class="h-5 w-5" />
            系统信息
          </h2>
          <button
            @click="refreshConfig"
            class="rounded-md border px-3 py-1.5 text-sm hover:bg-muted transition-colors flex items-center gap-1"
          >
            <RefreshCw class="h-4 w-4" />
            刷新
          </button>
        </div>
        
        <div v-if="systemInfo" class="grid gap-4 md:grid-cols-2">
          <div class="rounded-lg border p-4">
            <label class="text-sm text-muted-foreground">服务器地址</label>
            <p class="text-lg font-medium">{{ systemInfo.serverHost }}:{{ systemInfo.serverPort }}</p>
          </div>
          <div class="rounded-lg border p-4">
            <label class="text-sm text-muted-foreground">数据存储目录</label>
            <p class="text-lg font-medium">{{ systemInfo.chromaPersistDir }}</p>
          </div>
          <div class="rounded-lg border p-4">
            <label class="text-sm text-muted-foreground">日志级别</label>
            <p class="text-lg font-medium">{{ systemInfo.logLevel }}</p>
          </div>
          <div class="rounded-lg border p-4">
            <label class="text-sm text-muted-foreground">API 文档</label>
            <a 
              :href="`http://${systemInfo.serverHost === '0.0.0.0' ? 'localhost' : systemInfo.serverHost}:${systemInfo.serverPort}/docs`"
              target="_blank"
              class="text-lg font-medium text-primary hover:underline"
            >
              /docs
            </a>
          </div>
        </div>
      </div>

      <!-- MCP Config Export -->
      <div class="rounded-lg border bg-card p-6">
        <h2 class="text-lg font-semibold flex items-center gap-2 mb-4">
          <Download class="h-5 w-5" />
          MCP 配置导出
        </h2>
        
        <p class="text-muted-foreground text-sm mb-4">
          将以下配置添加到 Claude Desktop 的配置文件中，即可使用 RagHubMCP 作为 MCP 服务器。
        </p>

        <!-- Config Preview -->
        <div class="rounded-lg border bg-muted/30 p-4 overflow-auto">
          <pre class="text-sm">{{ JSON.stringify(mcpConfig, null, 2) }}</pre>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-3 mt-4">
          <button
            @click="copyMcpConfig"
            :disabled="copying"
            class="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {{ copying ? '复制中...' : '复制配置' }}
          </button>
          <button
            @click="downloadMcpConfig"
            class="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            下载配置文件
          </button>
          <span v-if="copyMessage" class="text-sm text-green-600">
            {{ copyMessage }}
          </span>
        </div>
      </div>

      <!-- Quick Links -->
      <div class="rounded-lg border bg-card p-6">
        <h2 class="text-lg font-semibold mb-4">快速链接</h2>
        <div class="grid gap-3 md:grid-cols-2">
          <a 
            href="https://github.com/AIRix315/RagHubMCP"
            target="_blank"
            class="rounded-lg border p-4 hover:bg-muted transition-colors"
          >
            <p class="font-medium">GitHub 仓库</p>
            <p class="text-sm text-muted-foreground">查看源码和提交 Issue</p>
          </a>
          <a 
            href="https://modelcontextprotocol.io/"
            target="_blank"
            class="rounded-lg border p-4 hover:bg-muted transition-colors"
          >
            <p class="font-medium">MCP 协议文档</p>
            <p class="text-sm text-muted-foreground">了解 Model Context Protocol</p>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>