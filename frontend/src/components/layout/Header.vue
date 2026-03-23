<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Menu, ChevronRight } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import ThemeSwitcher from '@/components/common/ThemeSwitcher.vue'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'
import { useSidebar } from '@/composables/useSidebar'

const { t } = useI18n()
const route = useRoute()
const { isMobile, openMobile } = useSidebar()

// Generate breadcrumb items from route
const breadcrumbs = computed(() => {
  const items: { label: string; path?: string }[] = []
  const pathSegments = route.path.split('/').filter(Boolean)
  
  // Map route names to labels
  const routeLabels: Record<string, string> = {
    'home': t('nav.home'),
    'config': t('nav.config'),
    'collections': t('nav.collections'),
    'benchmark': t('nav.benchmark'),
    'settings': t('nav.settings'),
    'providers': t('breadcrumb.providers'),
    'rerank': t('breadcrumb.rerank'),
    'pipeline': t('breadcrumb.pipeline'),
    'profiles': t('breadcrumb.profiles'),
    'test': t('breadcrumb.test'),
    'rerank-lab': t('nav.rerankLab'),
  }
  
  // Home is always first
  if (route.path !== '/') {
    items.push({ label: t('nav.home'), path: '/' })
  }
  
  // Build breadcrumb from path segments
  let currentPath = ''
  for (const segment of pathSegments) {
    currentPath += `/${segment}`
    const label = routeLabels[segment] || segment
    
    // Last item has no path (current page)
    if (currentPath === route.path) {
      items.push({ label })
    } else {
      items.push({ label, path: currentPath })
    }
  }
  
  // If we're on home, just show home
  if (items.length === 0) {
    items.push({ label: t('nav.home') })
  }
  
  return items
})

// Current page title
const pageTitle = computed(() => {
  return breadcrumbs.value[breadcrumbs.value.length - 1]?.label || ''
})
</script>

<template>
  <header
    class="sticky top-0 z-40 flex h-14 items-center gap-4 border-b border-header-border bg-header px-4 shadow-elevation-1"
  >
    <!-- Mobile menu button -->
    <Button
      v-if="isMobile"
      variant="ghost"
      size="icon"
      class="shrink-0 md:hidden"
      @click="openMobile"
    >
      <Menu class="h-5 w-5" />
      <span class="sr-only">{{ t('header.toggleMenu') }}</span>
    </Button>

    <!-- Breadcrumbs (hidden on mobile) -->
    <nav class="hidden md:flex items-center gap-1 text-sm">
      <template v-for="(item, index) in breadcrumbs" :key="index">
        <RouterLink
          v-if="item.path"
          :to="item.path"
          class="text-muted-foreground hover:text-foreground transition-colors"
        >
          {{ item.label }}
        </RouterLink>
        <span v-else class="font-medium text-foreground">
          {{ item.label }}
        </span>
        <ChevronRight
          v-if="index < breadcrumbs.length - 1"
          class="h-4 w-4 text-muted-foreground"
        />
      </template>
    </nav>

    <!-- Page title (mobile only) -->
    <h1 v-if="isMobile" class="flex-1 text-lg font-semibold truncate">
      {{ pageTitle }}
    </h1>

    <!-- Spacer -->
    <div class="flex-1" />

    <!-- Actions -->
    <div class="flex items-center gap-1">
      <LanguageSwitcher />
      <ThemeSwitcher />
    </div>
  </header>
</template>
