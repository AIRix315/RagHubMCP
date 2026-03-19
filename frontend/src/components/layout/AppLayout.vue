<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Home, Settings, Database, BarChart3, SlidersHorizontal } from 'lucide-vue-next'
</script>

<template>
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <aside class="w-64 border-r bg-muted/30">
      <div class="flex h-16 items-center border-b px-6">
        <h1 class="text-xl font-bold">RagHubMCP</h1>
      </div>
      <nav class="flex-1 space-y-1 p-4">
        <RouterLink
          to="/"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          active-class="bg-muted text-foreground"
        >
          <Home class="h-5 w-5" />
          首页
        </RouterLink>
        <RouterLink
          to="/config"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          active-class="bg-muted text-foreground"
        >
          <Settings class="h-5 w-5" />
          配置管理
        </RouterLink>
        <RouterLink
          to="/collections"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          active-class="bg-muted text-foreground"
        >
          <Database class="h-5 w-5" />
          Collections
        </RouterLink>
        <RouterLink
          to="/benchmark"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          active-class="bg-muted text-foreground"
        >
          <BarChart3 class="h-5 w-5" />
          效果对比
        </RouterLink>
        <RouterLink
          to="/settings"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          active-class="bg-muted text-foreground"
        >
          <SlidersHorizontal class="h-5 w-5" />
          系统设置
        </RouterLink>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="flex-1">
      <div class="container mx-auto p-6">
        <slot />
      </div>
    </main>
  </div>
</template>