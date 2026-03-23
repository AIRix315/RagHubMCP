<script setup lang="ts">
/**
 * AppLayout Component
 * 
 * 基于原型 simple.html 设计
 * 包含侧边栏导航、顶部工具栏、主题/语言切换
 */
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Home,
  Settings,
  Database,
  BarChart3,
  SlidersHorizontal,
  Languages,
  Sun,
  Moon,
  Zap
} from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'
import { useLocale } from '@/composables/useLocale'

const route = useRoute()
const { t } = useI18n()
const { isDark, toggleTheme } = useTheme()
const { locale, setLocale } = useLocale()

// 导航项
const navItems = [
  { path: '/', icon: Home, labelKey: 'nav.home' },
  { path: '/config', icon: Settings, labelKey: 'nav.config' },
  { path: '/collections', icon: Database, labelKey: 'nav.collections' },
  { path: '/benchmark', icon: BarChart3, labelKey: 'nav.benchmark' },
  { path: '/settings', icon: SlidersHorizontal, labelKey: 'nav.settings' }
]

// 服务状态（模拟）
const serverStatus = computed(() => ({
  running: true,
  address: 'localhost:8818'
}))

// 语言显示文本
const localeText = computed(() => locale.value === 'zh-CN' ? '中文' : 'EN')

// 切换语言
function toggleLang() {
  const newLocale = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  setLocale(newLocale)
}
</script>

<template>
  <div class="flex min-h-screen bg-background">
    <!-- Sidebar -->
    <aside class="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r bg-muted/30">
      <!-- Logo -->
      <div class="flex h-14 items-center gap-3 border-b px-4">
        <div class="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-primary to-primary/60">
          <Zap class="h-4 w-4 text-primary-foreground" />
        </div>
        <div>
          <div class="text-sm font-semibold">RagHubMCP</div>
          <div class="font-mono text-[10px] text-muted-foreground">v2.5.2</div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 space-y-1 overflow-y-auto p-3">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            route.path === item.path
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          ]"
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ t(item.labelKey) }}
        </RouterLink>
      </nav>

      <!-- Server Status -->
      <div class="border-t p-3">
        <div class="rounded-md bg-muted p-2.5">
          <div class="flex items-center gap-2 text-xs text-muted-foreground">
            <div 
              :class="[
                'h-1.5 w-1.5 rounded-full',
                serverStatus.running ? 'bg-green-500' : 'bg-red-500'
              ]" 
            />
            <span>{{ serverStatus.running ? t('home.tasks.activeDesc').split('，')[0] : t('common.error') }}</span>
          </div>
          <div class="mt-1 font-mono text-[10px] text-muted-foreground">
            {{ serverStatus.address }}
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex flex-1 flex-col ml-60">
      <!-- Header -->
      <header class="sticky top-0 z-30 flex h-14 items-center justify-end border-b bg-card px-5">
        <div class="flex items-center gap-2">
          <!-- Language Toggle -->
          <button
            class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            @click="toggleLang"
          >
            <Languages class="h-4 w-4" />
            <span class="text-xs">{{ localeText }}</span>
          </button>

          <!-- Theme Toggle -->
          <button
            class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            @click="toggleTheme"
          >
            <Sun v-if="isDark" class="h-4 w-4" />
            <Moon v-else class="h-4 w-4" />
          </button>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* 滚动条样式 */
aside::-webkit-scrollbar {
  width: 4px;
}

aside::-webkit-scrollbar-track {
  background: transparent;
}

aside::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 4px;
}

aside::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}
</style>